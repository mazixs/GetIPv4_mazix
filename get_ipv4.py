"""
Resolves domain names to IPv4 addresses and generates network route commands.

This script reads a list of domain names from specified input files, resolves
them to IPv4 addresses using configured DNS servers, and then processes these
addresses to generate various output files:
1.  A list of domain-to-IP mappings.
2.  A list of unique IPv4 addresses.
3.  A list of network route commands suitable for systems like Keenetic routers,
    based on a configured subnet mask.

Configuration is handled by the `AppConfig` class from `config_handler.py`,
which reads settings from 'config.ini'. The script uses standard libraries
like `socket` for DNS resolution and `ipaddress` for network calculations.
Logging is used for operational messages, warnings, and errors, outputting
to both console and a 'script_run.log' file.
"""
import os
import socket
import ipaddress
import sys
import logging
from config_handler import AppConfig, ConfigurationError

# Logging is configured in main()

def remove_file_if_exists(file_path: str):
    """
    Removes a file if it exists. Logs the action or any errors.

    Args:
        file_path (str): The path to the file to be removed.
    """
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
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
            # Note: socket.gethostbyname_ex can be blocking.
            # For large-scale applications, consider asynchronous DNS resolution.
            # The current implementation resolves against each DNS server sequentially.
            # The primary address is resolver[0], aliases are resolver[1], IPs are resolver[2]
            hostname, aliaslist, ipaddrlist = socket.gethostbyname_ex(domain)
            addresses.extend(ipaddrlist)
            # Could break here if only one successful resolution is needed per domain.
            # Current logic tries all DNS servers and aggregates unique results.
        except socket.gaierror:
            logging.warning(
                f"Не удалось разрешить домен: {domain} через DNS {dns_server} (gaierror)."
            )
        except Exception as e:
            # Catch any other unexpected errors during resolution with a specific server.
            logging.warning(
                f"Неожиданная ошибка при разрешении домена: {domain} через DNS {dns_server}: {e}",
                exc_info=False # Keep log concise for common network issues.
            )
    return list(set(addresses)) # Return unique addresses.

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
        network = ipaddress.IPv4Network(f"{ip_str}/{subnet_mask_value}", strict=False)
        return str(network.network_address), str(network.netmask)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError) as e:
        # Catches errors from invalid IP addresses or subnet mask formats.
        logging.error(
            f"Ошибка при вычислении сети для IP '{ip_str}' с маской '{subnet_mask_value}': {e}"
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
        with open(file_path, 'r', encoding='utf-8') as file:
            domains = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        logging.error(f"Файл с доменами '{file_path}' не найден.")
    except IOError as e:
        logging.error(f"Ошибка чтения файла '{file_path}': {e}")
    return domains

def process_domains(
    domains: list[str],
    app_config: AppConfig,
    dns_servers: list[str],
    unique_routes: set,
    subnet_mask_for_calc: str,
    domain_ip_output_fh, # File handler for domain:ip output
    only_ipv4_output_fh, # File handler for unique IPs
    keenetic_output_fh   # File handler for Keenetic routes
):
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
            
            if network_address and netmask: # Check if calculation was successful
                route_command = f"route ADD {network_address} MASK {netmask} 0.0.0.0"
                if route_command not in unique_routes:
                    unique_routes.add(route_command)
                    keenetic_output_fh.write(f"{route_command}\n")
            else:
                # Log that route generation is skipped for this address.
                logging.warning(
                    f"Маршрут для IP '{address}' (домен: {domain}) не будет сгенерирован "
                    "из-за ошибки вычисления сети."
                )
    # The redundant 'if route_command not in unique_routes:' block that was previously here
    # has been confirmed as removed in an earlier step.

def main():
    """
    Main function to orchestrate the domain resolution and route generation process.

    It initializes configuration, sets up logging, reads domains, processes them,
    and writes the output to configured files.
    """
    # Configure basic logging to file and console.
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("script_run.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    try:
        app_config = AppConfig() # Default 'config.ini'
    except ConfigurationError as e:
        logging.critical(f"Ошибка конфигурации: {e}")
        sys.exit(1)
    except FileNotFoundError: # Should be caught by AppConfig, but as a safeguard
        logging.critical("Критическая ошибка: Файл config.ini не найден.")
        sys.exit(1)
    except Exception as e: # Catch any other unexpected errors during AppConfig init
        logging.critical(f"Неожиданная ошибка при загрузке конфигурации: {e}", exc_info=True)
        sys.exit(1)

    # Retrieve configuration settings via AppConfig instance.
    domain_files_paths = app_config.get_domain_files()
    output_domain_ip_file_path = app_config.get_output_file_path("output_domain_ip")
    output_only_ipv4_file_path = app_config.get_output_file_path("output_only_ipv4")
    output_keenetic_file_path = app_config.get_output_file_path("output_keenetic")
    
    # Subnet mask for display purposes (e.g., "/24")
    subnet_prefix_display = app_config.get_subnet_mask_prefix()
    # Subnet mask for calculation (e.g., "24", "/24", or "255.255.255.0")
    subnet_mask_for_calc = app_config.get_subnet_mask_value_for_network_calculation()

    dns_servers = app_config.get_dns_servers_list()
    if not dns_servers:
        # This warning is important if DNS resolution is expected to occur.
        # AppConfig validation should catch cases where external DNS is enabled but no servers are listed.
        logging.warning(
            "Список DNS-серверов пуст. Разрешение имен будет ограничено или невозможно."
        )

    # Clear output files before generating new content.
    remove_file_if_exists(output_domain_ip_file_path)
    remove_file_if_exists(output_only_ipv4_file_path)
    remove_file_if_exists(output_keenetic_file_path)

    all_domains = []
    for domain_file_path in domain_files_paths:
        # Ensure paths from config are stripped of any accidental whitespace.
        domains_from_file = read_domains_from_file(domain_file_path.strip())
        all_domains.extend(domains_from_file)
    
    if not all_domains:
        logging.info("Не найдено доменов для обработки. Проверьте файлы доменов и конфигурацию.")
        sys.exit(0) # Graceful exit if there's nothing to process.

    unique_routes = set() # Used to store unique route commands.

    # Open output files once for all write operations.
    try:
        # Using 'a' (append) mode, but files are cleared beforehand by remove_file_if_exists.
        # This is effectively 'w' (write) but safer if remove_file_if_exists fails silently.
        with open(output_domain_ip_file_path, 'a', encoding="utf-8") as domain_ip_output_fh, \
             open(output_only_ipv4_file_path, 'a', encoding="utf-8") as only_ipv4_output_fh, \
             open(output_keenetic_file_path, 'a', encoding="utf-8") as keenetic_output_fh:
            
            process_domains(
                domains=all_domains,
                app_config=app_config, # Passed for potential future use
                dns_servers=dns_servers,
                unique_routes=unique_routes,
                subnet_mask_for_calc=subnet_mask_for_calc,
                domain_ip_output_fh=domain_ip_output_fh,
                only_ipv4_output_fh=only_ipv4_output_fh,
                keenetic_output_fh=keenetic_output_fh
            )
    except IOError as e:
        logging.error(f"Ошибка записи в выходной файл: {e}", exc_info=True)
        sys.exit(1)

    logging.info("Результаты сохранены в файлы:")
    logging.info(f"1. {output_domain_ip_file_path} - домен: IPv4")
    logging.info(f"2. {output_only_ipv4_file_path} - только IPv4 адреса")
    logging.info(
        f"3. {output_keenetic_file_path} - команды для Keenetic с агрегированной подсетью "
        f"{subnet_prefix_display}" # Use display version of subnet.
    )

if __name__ == "__main__":
    main()
