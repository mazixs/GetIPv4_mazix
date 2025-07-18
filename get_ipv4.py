from __future__ import annotations

import ipaddress
import logging
import os
import socket
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import TextIO

import dns.resolver
from config_handler import AppConfig, ConfigurationError

# Logging is configured in main()

def remove_file_if_exists(file_path: str):
    """
    Removes a file if it exists. Logs the action or any errors.

    Args:
        file_path (str): The path to the file to be removed.
    """
    path = Path(file_path)
    if path.exists():
        try:
            path.unlink()
            logging.info(f"Файл '{file_path}' удален.")
        except OSError as e:
            logging.error(f"Ошибка при удалении файла '{file_path}': {e}")

def get_ipv4_addresses(domain: str, dns_servers: list[str]) -> list[str]:
    """
    Resolves a domain name to a list of unique IPv4 addresses using specified DNS servers.

    It attempts to resolve the domain using each DNS server in the provided list.
    All successfully resolved unique IPv4 addresses are aggregated.

    Args:
        domain (str): The domain name to resolve.
        dns_servers (list[str]): A list of DNS server IP addresses to use for resolution.

    Returns:
        list[str]: A list of unique IPv4 addresses obtained for the domain.
                   Returns an empty list if resolution fails with all servers
                   or if the dns_servers list is empty.
    """
    if not dns_servers:
        logging.warning(
            f"Для домена '{domain}' список DNS-серверов пуст, разрешение невозможно."
        )
        return []

    addresses = []
    
    for dns_server in dns_servers:
        try:
            # Create a custom resolver for each DNS server
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            resolver.timeout = 5
            resolver.lifetime = 10
            
            # Query A records for IPv4 addresses
            answers = resolver.resolve(domain, 'A')
            for answer in answers:
                addresses.append(str(answer))
            
            logging.debug(f"DNS {dns_server}: разрешен домен {domain} -> {[str(a) for a in answers]}")
            
        except dns.resolver.NXDOMAIN:
            logging.warning(
                f"Домен {domain} не существует (NXDOMAIN) через DNS {dns_server}."
            )
        except dns.resolver.NoAnswer:
            logging.warning(
                f"Нет A-записей для домена {domain} через DNS {dns_server}."
            )
        except dns.resolver.Timeout:
            logging.warning(
                f"Таймаут при разрешении домена {domain} через DNS {dns_server}."
            )
        except Exception as e:
            # Catch any other unexpected errors during resolution with a specific server.
            logging.warning(
                f"Неожиданная ошибка при разрешении домена: {domain} через DNS {dns_server}: {e}",
                exc_info=False  # Keep log concise for common network issues.
            )
    return list(set(addresses))  # Return unique addresses.

def calculate_network(ip_str: str, subnet_mask_value: str) -> tuple[str | None, str | None]:
    """
    Calculates the network address and netmask from an IP address and subnet mask value.

    The subnet_mask_value can be a prefix length (e.g., "24"),
    a full netmask (e.g., "255.255.255.0"), or a CIDR prefix (e.g., "/24").

    Args:
        ip_str (str): The IP address string (e.g., "192.168.1.10").
        subnet_mask_value (str): The subnet mask string.

    Returns:
        tuple[str | None, str | None]: A tuple containing the network address string
                                       and netmask string. Returns (None, None) if
                                       calculation fails due to invalid input.
    """
    try:
        # Construct the network string in the format "ip/mask".
        # ipaddress.IPv4Network handles various mask formats like "24", "/24",
        # or "255.255.255.0".
        # strict=False allows the IP address to be a host address within the network.
        network = ipaddress.IPv4Network(
            f"{ip_str}/{subnet_mask_value}", strict=False
        )
        return str(network.network_address), str(network.netmask)
    except (
        ipaddress.AddressValueError,
        ipaddress.NetmaskValueError,
        ValueError
    ) as e:
        # Catches errors from invalid IP addresses or subnet mask formats.
        logging.error(
            f"Ошибка при вычислении сети для IP '{ip_str}' "
            f"с маской '{subnet_mask_value}': {e}"
        )
        return None, None

def read_domains_from_file(file_path: str) -> list[str]:
    """
    Reads domain names from a specified file.

    Each line in the file is expected to contain one domain name.
    Empty lines and leading/trailing whitespace are ignored.

    Args:
        file_path (str): The path to the file containing domain names.

    Returns:
        list[str]: A list of domain names read from the file. Returns an
                   empty list if the file is not found or an IOError occurs.
    """
    domains = []
    try:
        path = Path(file_path)
        content = path.read_text(encoding='utf-8')
        domains = [
            line.strip() for line in content.splitlines() if line.strip()
        ]
    except FileNotFoundError:
        logging.error(f"Файл с доменами '{file_path}' не найден.")
    except IOError as e:
        logging.error(f"Ошибка чтения файла '{file_path}': {e}")
    
    logging.info(f"Загружено {len(domains)} доменов из '{file_path}'.")
    return domains

def process_domains(
    domains: list[str],
    app_config: AppConfig,
    dns_servers: list[str],
    unique_routes: set[str],
    subnet_mask_for_calc: str,
    domain_ip_output_fh: TextIO,
    only_ipv4_output_fh: TextIO,
    keenetic_output_fh: TextIO,
) -> None:
    """
    Processes a list of domains: resolves them, calculates network routes, and writes results.

    For each domain, it resolves IPv4 addresses. For each address, it writes:
    1. Domain:IP mapping to `domain_ip_output_fh`.
    2. The IP address to `only_ipv4_output_fh`.
    3. A calculated route command to `keenetic_output_fh` if the route is unique.

    Args:
        domains (list[str]): A list of domain names to process.
        app_config (AppConfig): The application configuration object. (Currently unused in this func)
        dns_servers (list[str]): List of DNS servers to use for resolution.
        unique_routes (set): A set to store and check for uniqueness of route commands.
        subnet_mask_for_calc (str): The subnet mask value for network calculations.
        domain_ip_output_fh: Open file handler for domain:IP output.
        only_ipv4_output_fh: Open file handler for unique IPv4s output.
        keenetic_output_fh: Open file handler for Keenetic route commands output.
    """
    # The app_config argument is passed but not directly used in this function.
    # It might be intended for future use or could be removed if not needed.
    # For now, dns_servers and subnet_mask_for_calc are passed separately.

    for domain in domains:
        logging.info(f"Обрабатываю домен: {domain}")
        ipv4_addresses = get_ipv4_addresses(domain, dns_servers)

        for address in ipv4_addresses:
            domain_ip_output_fh.write(f"{domain}: {address}\n")
            only_ipv4_output_fh.write(f"{address}\n")

            network_address, netmask = calculate_network(address, subnet_mask_for_calc)
            
            if network_address and netmask:  # Check if calculation was successful
                route_command = (
                    f"route ADD {network_address} MASK {netmask} 0.0.0.0"
                )
                if route_command not in unique_routes:
                    unique_routes.add(route_command)
                    keenetic_output_fh.write(f"{route_command}\n")
            else:
                # Log that route generation is skipped for this address.
                logging.warning(
                    f"Маршрут для IP '{address}' (домен: {domain}) "
                    "не будет сгенерирован из-за ошибки вычисления сети."
                )
    # The redundant 'if route_command not in unique_routes:' block that was previously here
    # has been confirmed as removed in an earlier step.

def process_domains_monitoring(
    domains: list[str],
    dns_servers: list[str],
    unique_routes: set[str],
    seen_domain_ips: set[str],
    seen_ips: set[str],
    subnet_mask_for_calc: str,
    output_domain_ip_file_path: str,
    output_only_ipv4_file_path: str,
    output_keenetic_file_path: str,
    current_time: datetime,
) -> None:
    """
    Processes domains for monitoring mode, accumulating unique data over time.
    
    Only writes new unique combinations to avoid duplicates while preserving
    historical data across monitoring iterations.
    
    Args:
        domains: List of domain names to process
        dns_servers: List of DNS servers for resolution
        unique_routes: Set to track unique route commands
        seen_domain_ips: Set to track unique domain:IP combinations
        seen_ips: Set to track unique IP addresses
        subnet_mask_for_calc: Subnet mask for network calculations
        output_domain_ip_file_path: Path to domain:IP output file
        output_only_ipv4_file_path: Path to IP-only output file
        output_keenetic_file_path: Path to Keenetic routes output file
        current_time: Current timestamp for logging
    """
    new_domain_ips = []
    new_ips = []
    new_routes = []
    
    for domain in domains:
        logging.debug(f"Обрабатываю домен: {domain}")
        ipv4_addresses = get_ipv4_addresses(domain, dns_servers)
        
        for address in ipv4_addresses:
            domain_ip_combo = f"{domain}: {address}"
            
            # Check if this domain:IP combination is new
            if domain_ip_combo not in seen_domain_ips:
                seen_domain_ips.add(domain_ip_combo)
                new_domain_ips.append(domain_ip_combo)
            
            # Check if this IP is new
            if address not in seen_ips:
                seen_ips.add(address)
                new_ips.append(address)
            
            # Calculate route and check if it's new
            network_address, netmask = calculate_network(address, subnet_mask_for_calc)
            if network_address and netmask:
                route_command = (
                    f"route ADD {network_address} MASK {netmask} 0.0.0.0"
                )
                if route_command not in unique_routes:
                    unique_routes.add(route_command)
                    new_routes.append(route_command)
            else:
                logging.warning(
                    f"Маршрут для IP '{address}' (домен: {domain}) "
                    "не будет сгенерирован из-за ошибки вычисления сети."
                )
    
    # Write new data to files
    try:
        if new_domain_ips:
            with Path(output_domain_ip_file_path).open(
                'a', encoding="utf-8"
            ) as f:
                for entry in new_domain_ips:
                    f.write(f"{entry}\n")
            logging.info(
                f"Добавлено {len(new_domain_ips)} новых комбинаций домен:IP"
            )
        
        if new_ips:
            with Path(output_only_ipv4_file_path).open(
                'a', encoding="utf-8"
            ) as f:
                for entry in new_ips:
                    f.write(f"{entry}\n")
            logging.info(f"Добавлено {len(new_ips)} новых IP-адресов")
        
        if new_routes:
            with Path(output_keenetic_file_path).open(
                'a', encoding="utf-8"
            ) as f:
                for entry in new_routes:
                    f.write(f"{entry}\n")
            logging.info(f"Добавлено {len(new_routes)} новых маршрутов")
        
        if not new_domain_ips and not new_ips and not new_routes:
            logging.info("Новых данных не обнаружено в этой итерации")
            
    except IOError as e:
        logging.error(f"Ошибка записи в выходные файлы: {e}")

def main() -> None:
    """
    Main function to orchestrate the domain resolution and route generation process.

    It initializes configuration, sets up logging, reads domains, processes them,
    and writes the output to configured files. Supports monitoring mode for
    continuous data collection over a specified time period.
    """
    try:
        app_config = AppConfig()  # Default 'config.ini'
    except ConfigurationError as e:
        logging.critical(f"Ошибка конфигурации: {e}")
        sys.exit(1)
    except FileNotFoundError:  # Should be caught by AppConfig, but as a safeguard
        logging.critical("Критическая ошибка: Файл config.ini не найден.")
        sys.exit(1)
    except Exception as e:  # Catch any other unexpected errors during AppConfig init
        logging.critical(
            f"Неожиданная ошибка при загрузке конфигурации: {e}", exc_info=True
        )
        sys.exit(1)

    # Get log file path from config
    log_file_path = app_config.get_setting(
        'settings', 'log_file', 'result/script_run.log'
    )
    
    # Configure basic logging to file and console.
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Retrieve configuration settings via AppConfig instance.
    domain_files_paths = app_config.get_domain_files()
    output_domain_ip_file_path = app_config.get_output_file_path(
        "output_domain_ip"
    )
    output_only_ipv4_file_path = app_config.get_output_file_path(
        "output_only_ipv4"
    )
    output_keenetic_file_path = app_config.get_output_file_path(
        "output_keenetic"
    )
    
    # Subnet mask for display purposes (e.g., "/24")
    subnet_prefix_display = app_config.get_subnet_mask_prefix()
    # Subnet mask for calculation (e.g., "24", "/24", or "255.255.255.0")
    subnet_mask_for_calc = (
        app_config.get_subnet_mask_value_for_network_calculation()
    )

    # Get monitoring settings
    monitoring_duration_minutes = app_config.get_monitoring_duration_minutes()
    monitoring_interval_seconds = app_config.get_monitoring_interval_seconds()

    dns_servers = app_config.get_dns_servers_list()
    if not dns_servers:
        logging.warning(
            "Список DNS-серверов пуст. "
            "Разрешение имен будет ограничено или невозможно."
        )

    # Read all domains from files
    all_domains = []
    for domain_file_path in domain_files_paths:
        domains_from_file = read_domains_from_file(domain_file_path.strip())
        all_domains.extend(domains_from_file)
    
    if not all_domains:
        logging.info(
            "Не найдено доменов для обработки. "
            "Проверьте файлы доменов и конфигурацию."
        )
        sys.exit(0)

    # Initialize tracking sets for unique data
    unique_routes = set()
    seen_domain_ips = set()  # Track unique domain:IP combinations
    seen_ips = set()         # Track unique IP addresses

    # Create output directories if they don't exist
    Path(output_domain_ip_file_path).parent.mkdir(
        parents=True, exist_ok=True
    )
    Path(output_only_ipv4_file_path).parent.mkdir(
        parents=True, exist_ok=True
    )
    Path(output_keenetic_file_path).parent.mkdir(
        parents=True, exist_ok=True
    )

    # Initialize output files
    try:
        Path(output_domain_ip_file_path).write_text("", encoding="utf-8")
        Path(output_only_ipv4_file_path).write_text("", encoding="utf-8")
        Path(output_keenetic_file_path).write_text("", encoding="utf-8")
    except IOError as e:
        logging.error(f"Ошибка создания выходных файлов: {e}")
        sys.exit(1)

    if monitoring_duration_minutes > 0:
        logging.info("Запуск в режиме мониторинга")
        start_time = time.time()
        end_time = start_time + (monitoring_duration_minutes * 60)
        iteration = 0
        
        try:
            while time.time() < end_time:
                iteration += 1
                current_time = datetime.now()
                logging.info(
                    f"Итерация {iteration} мониторинга: {current_time}"
                )
                
                # Process domains and collect new data
                process_domains_monitoring(
                    domains=all_domains,
                    dns_servers=dns_servers,
                    unique_routes=unique_routes,
                    seen_domain_ips=seen_domain_ips,
                    seen_ips=seen_ips,
                    subnet_mask_for_calc=subnet_mask_for_calc,
                    output_domain_ip_file_path=output_domain_ip_file_path,
                    output_only_ipv4_file_path=output_only_ipv4_file_path,
                    output_keenetic_file_path=output_keenetic_file_path,
                    current_time=current_time
                )
                
                # Wait for next iteration if not the last one
                if time.time() + monitoring_interval_seconds < end_time:
                    time.sleep(monitoring_interval_seconds)
                else:
                    break
        except KeyboardInterrupt:
            logging.info(
                f"\nМониторинг прерван пользователем после {iteration} итераций."
            )
            
        logging.info(
            f"Мониторинг завершен. Обработано {iteration} итераций."
        )
    else:
        # Single run mode (legacy behavior)
        logging.info("Запуск в режиме однократного сбора данных")
        current_time = datetime.now()
        process_domains_monitoring(
            domains=all_domains,
            dns_servers=dns_servers,
            unique_routes=unique_routes,
            seen_domain_ips=seen_domain_ips,
            seen_ips=seen_ips,
            subnet_mask_for_calc=subnet_mask_for_calc,
            output_domain_ip_file_path=output_domain_ip_file_path,
            output_only_ipv4_file_path=output_only_ipv4_file_path,
            output_keenetic_file_path=output_keenetic_file_path,
            current_time=current_time
        )

    logging.info("Результаты сохранены в файлы:")
    logging.info(f"1. {output_domain_ip_file_path} - домен: IPv4")
    logging.info(f"2. {output_only_ipv4_file_path} - только IPv4 адреса")
    logging.info(
        f"3. {output_keenetic_file_path} - команды для Keenetic "
        f"с подсетью {subnet_prefix_display}"
    )
    logging.info(f"Уникальных маршрутов: {len(unique_routes)}")
    logging.info(f"Уникальных IP-адресов: {len(seen_ips)}")
    logging.info(
        f"Уникальных комбинаций домен:IP: {len(seen_domain_ips)}"
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info(
            "\nПрограмма была прервана пользователем (Ctrl+C). "
            "Завершение работы..."
        )
        sys.exit(0)
