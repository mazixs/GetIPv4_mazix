import os
import socket
import configparser
import ipaddress

# Функция для удаления файла, если он существует
def remove_file_if_exists(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Файл {file_path} удален.")

# Функция для чтения конфигурации из config.ini с указанием кодировки UTF-8
def load_config():
    config = configparser.ConfigParser()
    with open("config.ini", "r", encoding="utf-8") as f:
        config.read_file(f)
    return config

# Функция для получения списка DNS серверов
def get_dns_servers(config):
    dns_servers = []

    # Если включен локальный DNS
    if config.getint("settings", "use_local_dns") == 1:
        dns_servers.append("127.0.0.1")  # Локальный DNS

    # Если включены внешние DNS-серверы
    if config.getint("settings", "use_external_dns") == 1:
        external_dns_servers = config.get("settings", "dns_servers").split(',')
        dns_servers.extend(external_dns_servers)

    return dns_servers

# Получение IPv4 адресов через заданные DNS-серверы
def get_ipv4_addresses(domain, dns_servers):
    addresses = []
    for dns_server in dns_servers:
        try:
            resolver = socket.gethostbyname_ex(domain)
            addresses.extend(resolver[2])
        except socket.gaierror:
            print(f"Не удалось разрешить домен: {domain} через DNS {dns_server}")
    return list(set(addresses))  # Убираем дубли

# Функция для вычисления подсети и маски
def calculate_network(ip, subnet):
    network = ipaddress.IPv4Network(f"{ip}/{subnet}", strict=False)
    return str(network.network_address), str(network.netmask)

def main():
    # Загружаем конфигурацию
    config = load_config()

    # Считываем файлы с доменами
    domain_files = config.get("settings", "domains_files").split(',')
    output_domain_ip_file = config.get("settings", "output_domain_ip")
    output_only_ipv4_file = config.get("settings", "output_only_ipv4")
    output_keenetic_file = config.get("settings", "output_keenetic")
    subnet = config.get("settings", "subnet_mask")

    # Получаем DNS серверы для проверки
    dns_servers = get_dns_servers(config)

    # Очищаем файлы перед генерацией новых
    for file in [output_domain_ip_file, output_only_ipv4_file, output_keenetic_file]:
        remove_file_if_exists(file)

    unique_routes = set()

    # Обрабатываем каждый файл с доменами
    for domain_file in domain_files:
        try:
            with open(domain_file.strip(), 'r') as file:
                domains = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            print(f"Файл {domain_file} не найден.")
            continue

        with open(output_domain_ip_file, 'a', encoding="utf-8") as domain_ip_output, \
             open(output_only_ipv4_file, 'a', encoding="utf-8") as only_ipv4_output, \
             open(output_keenetic_file, 'a', encoding="utf-8") as keenetic_output:

            for domain in domains:
                print(f"Обрабатываю домен: {domain}")
                ipv4_addresses = get_ipv4_addresses(domain, dns_servers)

                for address in ipv4_addresses:
                    domain_ip_output.write(f"{domain}: {address}\n")
                    only_ipv4_output.write(f"{address}\n")

                    # Вычисляем подсеть и маску
                    network_address, netmask = calculate_network(address, subnet.strip('/'))
                    route_command = f"route ADD {network_address} MASK {netmask} 0.0.0.0"

                    if route_command not in unique_routes:
                        unique_routes.add(route_command)
                        keenetic_output.write(f"{route_command}\n")

    print("Результаты сохранены в файлы:")
    print(f"1. {output_domain_ip_file} - домен: IPv4")
    print(f"2. {output_only_ipv4_file} - только IPv4 адреса")
    print(f"3. {output_keenetic_file} - команды для Keenetic с агрегированной подсетью {subnet}")

if __name__ == "__main__":
    main()
