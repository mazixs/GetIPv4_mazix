import unittest
from unittest.mock import patch, mock_open
import configparser
import logging

# Assuming config_handler.py is in the parent directory or accessible via PYTHONPATH
from config_handler import AppConfig, ConfigurationError

# Suppress logging output during tests by default
logging.disable(logging.CRITICAL)

class TestAppConfig(unittest.TestCase):

    def create_mock_config_content(self, settings_dict):
        parser = configparser.ConfigParser()
        if settings_dict: # Ensure there's at least one section if dict is not empty
            parser['settings'] = settings_dict
        
        from io import StringIO
        string_io = StringIO()
        parser.write(string_io)
        return string_io.getvalue()

    def base_settings(self):
        return {
            'use_local_dns': '1',
            'use_external_dns': '1',
            'dns_servers': '8.8.8.8,1.1.1.1',
            'domains_files': 'domains1.txt,domains2.txt',
            'output_domain_ip': 'out_domain_ip.txt',
            'output_only_ipv4': 'out_ipv4.txt',
            'output_keenetic': 'out_keenetic.txt',
            'subnet_mask': '24',
        }

    @patch('config_handler.open', new_callable=mock_open)
    @patch('configparser.ConfigParser.read')
    def test_valid_config_loads_successfully(self, mock_read, mock_file_open):
        valid_content = self.create_mock_config_content(self.base_settings())
        mock_file_open.return_value.read.return_value = valid_content # for read_file
        
        # Simulate successful read for config.read(file)
        # We need to patch ConfigParser.read to simulate it reading the file successfully
        # The actual .read() method of ConfigParser is what processes the content.
        # We are mocking open, so ConfigParser().read(filename) needs to be "tricked"
        # or we directly make ConfigParser().read_file(stream) work.
        
        # Let's refine the mock for open to provide content for read_file
        m_open = mock_open(read_data=valid_content)
        with patch('builtins.open', m_open):
             # Patch ConfigParser's read method to simulate it parsing the file successfully
            with patch.object(configparser.ConfigParser, 'read_file', return_value=None) as mock_read_file_method:
                # This is tricky because read_file is called on the instance.
                # Instead, we'll mock the __init__ of AppConfig to use a pre-loaded parser
                
                parser_instance = configparser.ConfigParser()
                parser_instance.read_string(valid_content) # Load content directly

                with patch('configparser.ConfigParser') as mock_parser_class:
                    mock_parser_class.return_value = parser_instance # Return our pre-loaded instance
                    try:
                        app_config = AppConfig('dummy_config.ini')
                        self.assertIsNotNone(app_config)
                        # Check a few values
                        self.assertEqual(app_config.get_use_local_dns(), 1)
                        self.assertEqual(app_config.get_subnet_mask_value_for_network_calculation(), '24')
                        self.assertEqual(app_config.get_subnet_mask_prefix(), '/24')
                    except ConfigurationError as e:
                        self.fail(f"Valid config raised ConfigurationError: {e}")


    def test_missing_config_file(self):
        with patch('builtins.open', mock_open()) as m_open:
            m_open.side_effect = FileNotFoundError("File not found")
            with self.assertRaisesRegex(ConfigurationError, "Configuration file .* not found."):
                AppConfig('non_existent_config.ini')

    def test_empty_config_file(self):
        m_open = mock_open(read_data="")
        with patch('builtins.open', m_open):
            with self.assertRaisesRegex(ConfigurationError, "Configuration file .* is empty or not a valid INI format."):
                 AppConfig('empty_config.ini')


    def run_validation_test(self, settings_override, error_message_regex):
        config_settings = self.base_settings()
        config_settings.update(settings_override)
        content = self.create_mock_config_content(config_settings)
        
        parser_instance = configparser.ConfigParser()
        parser_instance.read_string(content)

        with patch('configparser.ConfigParser') as mock_parser_class:
            mock_parser_class.return_value = parser_instance
            with self.assertRaisesRegex(ConfigurationError, error_message_regex):
                AppConfig('test_config.ini')
    
    def test_missing_settings_section(self):
        content = "[other_section]\nkey=value" # No [settings]
        parser_instance = configparser.ConfigParser()
        parser_instance.read_string(content)
        with patch('configparser.ConfigParser') as mock_parser_class:
            mock_parser_class.return_value = parser_instance
            with self.assertRaisesRegex(ConfigurationError, "Missing \\[settings\\] section"):
                AppConfig('test_config.ini')


    def test_invalid_use_local_dns(self):
        self.run_validation_test({'use_local_dns': '3'}, "'use_local_dns' in \\[settings\\] must be 0 or 1")

    def test_missing_dns_servers_if_external_dns_used(self):
        self.run_validation_test({'use_external_dns': '1', 'dns_servers': ''}, 
                                 "'dns_servers' in \\[settings\\] must be non-empty if 'use_external_dns' is 1")

    def test_valid_dns_servers_empty_if_external_dns_not_used(self):
        settings = self.base_settings()
        settings['use_external_dns'] = '0'
        settings['dns_servers'] = '' # This is now valid
        content = self.create_mock_config_content(settings)
        parser_instance = configparser.ConfigParser()
        parser_instance.read_string(content)
        with patch('configparser.ConfigParser') as mock_parser_class:
            mock_parser_class.return_value = parser_instance
            try:
                app_config = AppConfig('test_config.ini')
                self.assertEqual(app_config.get_dns_servers_list(), ['127.0.0.1']) # Only local
            except ConfigurationError:
                self.fail("Configuration should be valid when external DNS is off and dns_servers is empty.")


    def test_missing_domains_files(self):
        self.run_validation_test({'domains_files': ''}, "'domains_files' in \\[settings\\] must be a non-empty string.")

    def test_missing_output_domain_ip(self):
        self.run_validation_test({'output_domain_ip': ''}, "'output_domain_ip' in \\[settings\\] section must be a non-empty string.")

    def test_invalid_subnet_mask_format(self):
        self.run_validation_test({'subnet_mask': 'invalid_mask'}, 
                                 "'subnet_mask' .* is not a valid prefix .* or a full netmask")
        self.run_validation_test({'subnet_mask': '/33'}, 
                                 "'subnet_mask' .* is not a valid prefix .* or a full netmask")
        self.run_validation_test({'subnet_mask': '255.255.255.256'},
                                 "'subnet_mask' .* is not a valid prefix .* or a full netmask")


    def test_getters_with_valid_data(self):
        settings = self.base_settings()
        content = self.create_mock_config_content(settings)
        parser_instance = configparser.ConfigParser()
        parser_instance.read_string(content)

        with patch('configparser.ConfigParser') as mock_parser_class:
            mock_parser_class.return_value = parser_instance
            app_config = AppConfig('test_config.ini')

            self.assertEqual(app_config.get_use_local_dns(), 1)
            self.assertEqual(app_config.get_use_external_dns(), 1)
            self.assertCountEqual(app_config.get_dns_servers_list(), ['127.0.0.1', '8.8.8.8', '1.1.1.1'])
            self.assertCountEqual(app_config.get_domain_files(), ['domains1.txt', 'domains2.txt'])
            self.assertEqual(app_config.get_output_file_path('output_domain_ip'), 'out_domain_ip.txt')
            self.assertEqual(app_config.get_subnet_mask_value_for_network_calculation(), '24')
            self.assertEqual(app_config.get_subnet_mask_prefix(), '/24')

            # Test with full subnet mask
            settings['subnet_mask'] = '255.255.255.0'
            content = self.create_mock_config_content(settings)
            parser_instance_2 = configparser.ConfigParser()
            parser_instance_2.read_string(content)
            mock_parser_class.return_value = parser_instance_2
            app_config_2 = AppConfig('test_config.ini')
            self.assertEqual(app_config_2.get_subnet_mask_value_for_network_calculation(), '255.255.255.0')
            self.assertEqual(app_config_2.get_subnet_mask_prefix(), '/24')

            # Test with CIDR subnet mask
            settings['subnet_mask'] = '/27'
            content = self.create_mock_config_content(settings)
            parser_instance_3 = configparser.ConfigParser()
            parser_instance_3.read_string(content)
            mock_parser_class.return_value = parser_instance_3
            app_config_3 = AppConfig('test_config.ini')
            self.assertEqual(app_config_3.get_subnet_mask_value_for_network_calculation(), '/27')
            self.assertEqual(app_config_3.get_subnet_mask_prefix(), '/27')


    def test_dns_servers_list_logic(self):
        parser_instance = configparser.ConfigParser()
        with patch('configparser.ConfigParser') as mock_parser_class:
            mock_parser_class.return_value = parser_instance
            
            # Case 1: Local only
            settings = self.base_settings()
            settings['use_local_dns'] = '1'
            settings['use_external_dns'] = '0'
            settings['dns_servers'] = '' # Should be ignored
            parser_instance.read_string(self.create_mock_config_content(settings))
            app_config = AppConfig('test.ini')
            self.assertEqual(app_config.get_dns_servers_list(), ['127.0.0.1'])

            # Case 2: External only
            settings['use_local_dns'] = '0'
            settings['use_external_dns'] = '1'
            settings['dns_servers'] = '1.1.1.1,2.2.2.2'
            parser_instance.read_string(self.create_mock_config_content(settings)) # re-read
            app_config = AppConfig('test.ini') # re-init
            self.assertCountEqual(app_config.get_dns_servers_list(), ['1.1.1.1', '2.2.2.2'])

            # Case 3: Both local and external (duplicates should be handled by set)
            settings['use_local_dns'] = '1'
            settings['use_external_dns'] = '1'
            settings['dns_servers'] = '127.0.0.1,8.8.8.8' # 127.0.0.1 is duplicated
            parser_instance.read_string(self.create_mock_config_content(settings))
            app_config = AppConfig('test.ini')
            self.assertCountEqual(app_config.get_dns_servers_list(), ['127.0.0.1', '8.8.8.8'])

            # Case 4: Neither (should be empty, though main script warns)
            settings['use_local_dns'] = '0'
            settings['use_external_dns'] = '0'
            settings['dns_servers'] = ''
            parser_instance.read_string(self.create_mock_config_content(settings))
            app_config = AppConfig('test.ini')
            self.assertEqual(app_config.get_dns_servers_list(), [])

if __name__ == '__main__':
    logging.disable(logging.NOTSET) # Re-enable logging if running standalone for debugging
    unittest.main()
