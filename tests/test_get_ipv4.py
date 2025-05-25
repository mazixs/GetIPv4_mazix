import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import socket
import ipaddress # Required for calculate_network tests, though not explicitly imported in get_ipv4.py directly
import logging

# Assuming get_ipv4.py is in the parent directory or accessible via PYTHONPATH
# This might require adjusting sys.path if running tests directly from the tests directory
# For `python -m unittest discover tests`, it usually works if tests is a package.
import get_ipv4 

# Suppress logging output during tests by default
logging.disable(logging.CRITICAL)

class TestGetIPv4Utils(unittest.TestCase):

    @patch('os.path.exists')
    @patch('os.remove')
    @patch('logging.info')
    @patch('logging.error')
    def test_remove_file_if_exists(self, mock_log_error, mock_log_info, mock_os_remove, mock_os_path_exists):
        # Test case 1: File exists and is removed
        mock_os_path_exists.return_value = True
        get_ipv4.remove_file_if_exists("test_file.txt")
        mock_os_path_exists.assert_called_once_with("test_file.txt")
        mock_os_remove.assert_called_once_with("test_file.txt")
        mock_log_info.assert_called_once_with("Файл test_file.txt удален.")
        mock_log_error.assert_not_called()

        # Reset mocks for next case
        mock_os_path_exists.reset_mock()
        mock_os_remove.reset_mock()
        mock_log_info.reset_mock()

        # Test case 2: File does not exist
        mock_os_path_exists.return_value = False
        get_ipv4.remove_file_if_exists("test_file.txt")
        mock_os_path_exists.assert_called_once_with("test_file.txt")
        mock_os_remove.assert_not_called()
        mock_log_info.assert_not_called() # No log if file doesn't exist to remove
        mock_log_error.assert_not_called()
        
        mock_os_path_exists.reset_mock()
        mock_log_error.reset_mock()

        # Test case 3: OSError during removal
        mock_os_path_exists.return_value = True
        mock_os_remove.side_effect = OSError("Permission denied")
        get_ipv4.remove_file_if_exists("test_file.txt")
        mock_os_remove.assert_called_once_with("test_file.txt")
        mock_log_error.assert_called_once_with("Ошибка при удалении файла 'test_file.txt': Permission denied")
        mock_log_info.assert_not_called() # No success log if error


    @patch('socket.gethostbyname_ex')
    @patch('logging.warning')
    def test_get_ipv4_addresses(self, mock_log_warning, mock_gethostbyname_ex):
        domain = "example.com"
        dns_servers = ["8.8.8.8", "1.1.1.1"]

        # Test case 1: Successful resolution
        mock_gethostbyname_ex.return_value = (domain, [], ["192.0.2.1", "192.0.2.2"])
        result = get_ipv4.get_ipv4_addresses(domain, dns_servers)
        self.assertCountEqual(result, ["192.0.2.1", "192.0.2.2"])
        self.assertEqual(mock_gethostbyname_ex.call_count, 2) # Called for each DNS
        mock_log_warning.assert_not_called()

        mock_gethostbyname_ex.reset_mock()
        
        # Test case 2: socket.gaierror
        mock_gethostbyname_ex.side_effect = socket.gaierror("Resolution failed")
        result = get_ipv4.get_ipv4_addresses(domain, dns_servers)
        self.assertEqual(result, [])
        self.assertEqual(mock_gethostbyname_ex.call_count, 2)
        mock_log_warning.assert_any_call(f"Не удалось разрешить домен: {domain} через DNS {dns_servers[0]} (gaierror).")
        mock_log_warning.assert_any_call(f"Не удалось разрешить домен: {domain} через DNS {dns_servers[1]} (gaierror).")
        
        mock_gethostbyname_ex.reset_mock()
        mock_log_warning.reset_mock()

        # Test case 3: Empty dns_servers list
        result = get_ipv4.get_ipv4_addresses(domain, [])
        self.assertEqual(result, [])
        mock_gethostbyname_ex.assert_not_called()
        mock_log_warning.assert_called_once_with(f"Для домена '{domain}' список DNS-серверов пуст, разрешение невозможно.")

        mock_log_warning.reset_mock()

        # Test case 4: General exception during resolution
        mock_gethostbyname_ex.side_effect = Exception("Some other error")
        result = get_ipv4.get_ipv4_addresses(domain, dns_servers)
        self.assertEqual(result, [])
        self.assertEqual(mock_gethostbyname_ex.call_count, 2)
        mock_log_warning.assert_any_call(f"Неожиданная ошибка при разрешении домена: {domain} через DNS {dns_servers[0]}: Some other error", exc_info=False)


    @patch('logging.error')
    def test_calculate_network(self, mock_log_error):
        # Test case 1: Valid IP and subnet prefix
        ip = "192.168.1.10"
        subnet = "24" # Prefix length
        network_addr, netmask = get_ipv4.calculate_network(ip, subnet)
        self.assertEqual(network_addr, "192.168.1.0")
        self.assertEqual(netmask, "255.255.255.0")
        mock_log_error.assert_not_called()

        # Test case 2: Valid IP and full netmask
        subnet_full = "255.255.255.0"
        network_addr, netmask = get_ipv4.calculate_network(ip, subnet_full)
        self.assertEqual(network_addr, "192.168.1.0")
        self.assertEqual(netmask, "255.255.255.0")
        mock_log_error.assert_not_called()

        # Test case 3: Valid IP and CIDR subnet
        subnet_cidr = "/24"
        network_addr, netmask = get_ipv4.calculate_network(ip, subnet_cidr)
        self.assertEqual(network_addr, "192.168.1.0")
        self.assertEqual(netmask, "255.255.255.0")
        mock_log_error.assert_not_called()


        # Test case 4: Invalid IP address
        invalid_ip = "999.999.999.999"
        network_addr, netmask = get_ipv4.calculate_network(invalid_ip, subnet)
        self.assertIsNone(network_addr)
        self.assertIsNone(netmask)
        mock_log_error.assert_called_once()
        self.assertIn(f"Ошибка при вычислении сети для IP '{invalid_ip}' с маской '{subnet}'", mock_log_error.call_args[0][0])
        
        mock_log_error.reset_mock()

        # Test case 5: Invalid subnet mask
        invalid_subnet = "33" # Invalid prefix length
        network_addr, netmask = get_ipv4.calculate_network(ip, invalid_subnet)
        self.assertIsNone(network_addr)
        self.assertIsNone(netmask)
        mock_log_error.assert_called_once()
        self.assertIn(f"Ошибка при вычислении сети для IP '{ip}' с маской '{invalid_subnet}'", mock_log_error.call_args[0][0])
        
        mock_log_error.reset_mock()
        
        invalid_subnet_full = "255.255.255.256"
        network_addr, netmask = get_ipv4.calculate_network(ip, invalid_subnet_full)
        self.assertIsNone(network_addr)
        self.assertIsNone(netmask)
        mock_log_error.assert_called_once()
        self.assertIn(f"Ошибка при вычислении сети для IP '{ip}' с маской '{invalid_subnet_full}'", mock_log_error.call_args[0][0])


    @patch('builtins.open', new_callable=mock_open)
    @patch('logging.error')
    def test_read_domains_from_file(self, mock_log_error, mock_file_open):
        file_path = "domains.txt"

        # Test case 1: Valid file with domains
        mock_file_open.return_value.read.return_value = "example.com\nsub.example.com\n\n another.com "
        domains = get_ipv4.read_domains_from_file(file_path)
        self.assertEqual(domains, ["example.com", "sub.example.com", "another.com"])
        mock_file_open.assert_called_once_with(file_path, 'r', encoding='utf-8')
        mock_log_error.assert_not_called()
        
        mock_file_open.reset_mock() # Reset for the next call if needed within the same test

        # Test case 2: Empty file
        mock_file_open.return_value.read.return_value = ""
        domains = get_ipv4.read_domains_from_file(file_path)
        self.assertEqual(domains, [])
        mock_log_error.assert_not_called()
        
        mock_file_open.reset_mock()

        # Test case 3: FileNotFoundError
        mock_file_open.side_effect = FileNotFoundError("File not found")
        domains = get_ipv4.read_domains_from_file(file_path)
        self.assertEqual(domains, [])
        mock_log_error.assert_called_once_with(f"Файл с доменами '{file_path}' не найден.")
        
        mock_log_error.reset_mock()
        mock_file_open.side_effect = None # Reset side effect

        # Test case 4: Other IOError
        mock_file_open.side_effect = IOError("Permission denied")
        domains = get_ipv4.read_domains_from_file(file_path)
        self.assertEqual(domains, [])
        mock_log_error.assert_called_once_with(f"Ошибка чтения файла '{file_path}': Permission denied")

if __name__ == '__main__':
    logging.disable(logging.NOTSET) # Re-enable logging for standalone debugging
    unittest.main()
