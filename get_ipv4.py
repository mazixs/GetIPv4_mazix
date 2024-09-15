import os
import socket

def remove_file_if_exists(file_path):
    """Удаляет файл, если он существует."""
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Файл {file_path} удален.")

def get_ipv4_addresses(domain):
    """Получает все IPv4 адреса для заданного домена."""
    try:
        return socket.gethostbyname_ex(domain)[2]
    except socket.gaierror:
        print(f"Не удалось разрешить домен: {domain}")
        return []

def main():
    # Определяем имена файлов
    domains_file = "domains.txt"
    result_domain_ip_file = "result_domain_ip.txt"
    result_onlyipv4_file = "result_onlyipv4.txt"
    result_keenetic_file = "result_keenetic.txt"
    mask = '255.255.255.255'

    # Очищаем файлы перед генерацией новых
    for file in [result_domain_ip_file, result_onlyipv4_file, result_keenetic_file]:
        remove_file_if_exists(file)

    try:
        with open(domains_file, 'r') as file:
            domains = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Файл {domains_file} не найден.")
        return

    unique_routes = set()

    with open(result_domain_ip_file, 'w') as domain_ip_output, \
         open(result_onlyipv4_file, 'w') as only_ipv4_output, \
         open(result_keenetic_file, 'w') as keenetic_output:

        for domain in domains:
            print(f"Обрабатываю домен: {domain}")
            ipv4_addresses = get_ipv4_addresses(domain)

            for address in ipv4_addresses:
                domain_ip_output.write(f"{domain}: {address}\n")
                only_ipv4_output.write(f"{address}\n")

                route_command = f"route ADD {address} MASK {mask} 0.0.0.0"
                if route_command not in unique_routes:
                    unique_routes.add(route_command)
                    keenetic_output.write(f"{route_command}\n")

    print("Результаты сохранены в файлы:")
    print(f"1. {result_domain_ip_file} - домен: IPv4")
    print(f"2. {result_onlyipv4_file} - только IPv4 адреса")
    print(f"3. {result_keenetic_file} - команды для Keenetic с подсетью /32")

if __name__ == "__main__":
    main()
    