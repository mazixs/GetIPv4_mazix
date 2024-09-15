import socket

def get_ipv4_addresses(domain):
    try:
        # Получение информации по домену
        addresses = socket.gethostbyname_ex(domain)[2]
        return addresses
    except socket.gaierror:
        print(f"Не удалось разрешить домен: {domain}")
        return []

def main():
    # Имя файла с доменами и файлы для сохранения результатов
    domains_file = "domains.txt"
    result_domain_ip_file = "result_domain_ip.txt"
    result_onlyipv4_file = "result_onlyipv4.txt"
    result_keenetic_file = "result_keenetic.txt"

    # Определяем маску для всех IP-адресов как /32
    subnet = '32'
    mask = '255.255.255.255'

    try:
        # Чтение доменов из файла
        with open(domains_file, 'r') as file:
            domains = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print(f"Файл {domains_file} не найден.")
        return

    with open(result_domain_ip_file, 'w') as domain_ip_output, \
         open(result_onlyipv4_file, 'w') as only_ipv4_output, \
         open(result_keenetic_file, 'w') as keenetic_output:

        # Сет для уникальных маршрутов
        unique_routes = set()

        # Обработка каждого домена
        for domain in domains:
            if domain:
                print(f"Обрабатываю домен: {domain}")
                ipv4_addresses = get_ipv4_addresses(domain)
                for address in ipv4_addresses:
                    # Запись в файлы с разными форматами
                    domain_ip_output.write(f"{domain}: {address}\n")
                    only_ipv4_output.write(f"{address}\n")

                    # Формируем команду маршрутизации для /32
                    route_command = f"route ADD {address}/{subnet} MASK {mask} 0.0.0.0"
                    
                    # Проверяем уникальность маршрута и добавляем в файл
                    if route_command not in unique_routes:
                        unique_routes.add(route_command)
                        keenetic_output.write(f"{route_command}\n")

    print("Результаты сохранены в файлы:")
    print(f"1. {result_domain_ip_file} - домен: IPv4")
    print(f"2. {result_onlyipv4_file} - только IPv4 адреса")
    print(f"3. {result_keenetic_file} - команды для Keenetic с подсетью /32")

if __name__ == "__main__":
    main()
