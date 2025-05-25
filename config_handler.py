"""
Manages application configuration using an INI file (config.ini).

This module defines the `AppConfig` class, which is responsible for loading,
validating, and providing access to configuration settings required by the
main application. It uses the `configparser` module to read INI files
and the `ipaddress` module for validating network-related configurations.
A custom `ConfigurationError` exception is raised for any issues related
to configuration loading or validation, ensuring that the application
does not run with invalid settings.
"""
import configparser
import ipaddress
import logging

# Standard library logging, no specific configuration here,
# as it's handled by the main script.

class ConfigurationError(ValueError):
    """
    Custom exception raised for errors in configuration loading or validation.

    Inherits from ValueError, indicating that an inappropriate value was
    encountered in the configuration.
    """
    pass

class AppConfig:
    """
    Handles loading, validation, and access to application settings from a config file.

    The class expects a configuration file (defaulting to 'config.ini') with
    a '[settings]' section containing various operational parameters. It validates
    these parameters upon initialization and provides getter methods to access them.
    Raises ConfigurationError if the config file is missing, malformed, or contains
    invalid or missing settings.
    """

    def __init__(self, config_file: str = 'config.ini'):
        """
        Initializes the AppConfig object by loading and validating the configuration.

        Args:
            config_file (str): The path to the configuration file.
                               Defaults to 'config.ini'.

        Raises:
            ConfigurationError: If the configuration file cannot be found,
                                is empty, malformed, or if any setting fails validation.
        """
        self.config = configparser.ConfigParser()
        self.config_file_path = config_file # Store for error messages

        try:
            # Attempt to read with UTF-8 encoding first, common for modern configs.
            with open(config_file, "r", encoding="utf-8") as f:
                self.config.read_file(f)
        except UnicodeDecodeError:
            # Fallback to system's default encoding if UTF-8 fails.
            # This is a pragmatic choice, though explicit encoding is preferred.
            if not self.config.read(config_file, encoding=None): # encoding=None uses locale default
                 raise ConfigurationError(
                    f"Configuration file '{config_file}' not found or is empty (even with default encoding)."
                )
        except FileNotFoundError:
             raise ConfigurationError(f"Configuration file '{config_file}' not found.")

        # Ensure the configuration file was not just empty or an invalid INI format.
        if not self.config.sections():
            raise ConfigurationError(
                f"Configuration file '{config_file}' is empty or not a valid INI format."
            )

        self._validate_config()

    def _validate_config(self):
        """
        Performs comprehensive validation of all required configuration settings.

        This private method is called during initialization to ensure that all
        necessary sections and options are present and have valid values.

        Raises:
            ConfigurationError: If any configuration setting is missing or invalid.
        """
        if not self.config.has_section('settings'):
            raise ConfigurationError("Missing [settings] section in configuration file.")

        # Validate boolean-like integers (0 or 1)
        for option in ['use_local_dns', 'use_external_dns']:
            # Using a fallback that's clearly not 0 or 1 to detect missing or non-integer values.
            value = self.config.getint('settings', option, fallback=-1)
            if value not in [0, 1]:
                actual_value = self.config.get('settings', option, fallback='<not found>')
                raise ConfigurationError(
                    f"'{option}' in [settings] must be 0 or 1. Found: '{actual_value}'"
                )

        # Validate 'dns_servers' if external DNS is enabled.
        if self.get_use_external_dns() == 1:
            if not self.config.get('settings', 'dns_servers', fallback='').strip():
                raise ConfigurationError(
                    "'dns_servers' in [settings] must be non-empty if 'use_external_dns' is 1."
                )

        # Validate that 'domains_files' is a non-empty string.
        if not self.config.get('settings', 'domains_files', fallback='').strip():
            raise ConfigurationError("'domains_files' in [settings] must be a non-empty string.")

        # Validate output file paths (must be non-empty strings).
        # These are expected in the [settings] section as per current usage in get_ipv4.py.
        for option in ['output_domain_ip', 'output_only_ipv4', 'output_keenetic']:
            if not self.config.get('settings', option, fallback='').strip():
                raise ConfigurationError(
                    f"'{option}' in [settings] section must be a non-empty string."
                )
        
        self._validate_subnet_mask()

    def _validate_subnet_mask(self):
        """
        Validates the 'subnet_mask' setting.

        The subnet mask must be a non-empty string and represent a valid IPv4
        subnet mask, either as a prefix length (e.g., "24"), a CIDR prefix
        (e.g., "/24"), or a full netmask string (e.g., "255.255.255.0").

        Raises:
            ConfigurationError: If 'subnet_mask' is missing or invalid.
        """
        subnet_mask_value = self.get_subnet_mask_value_for_network_calculation()
        if not subnet_mask_value:
            raise ConfigurationError("'subnet_mask' in [settings] section must be a non-empty string.")
        
        # The ipaddress library is used for validation. If it can parse the value
        # (as part of a dummy network string), it's considered valid.
        try:
            # strict=False allows host bits to be set in the address part,
            # which is fine for just validating the mask part.
            ipaddress.IPv4Network(f'0.0.0.0/{subnet_mask_value}', strict=False)
        except ValueError: # Catches malformed prefix or netmask strings.
            raise ConfigurationError(
                f"'subnet_mask' ('{subnet_mask_value}') in [settings] is not a valid prefix (e.g., 24), "
                f"a full netmask (e.g., 255.255.255.0), or a CIDR prefix (e.g., /24)."
            )

    def get_setting(self, section: str, key: str, fallback=None) -> str | None:
        """
        Retrieves a string setting from the specified section and key.

        Args:
            section (str): The section name in the INI file.
            key (str): The key (option name) within the section.
            fallback: The value to return if the key is not found. Defaults to None.

        Returns:
            str | None: The configuration value as a string, or the fallback value.
        """
        return self.config.get(section, key, fallback=fallback)

    def get_int_setting(self, section: str, key: str, fallback=None) -> int | None:
        """
        Retrieves an integer setting from the specified section and key.

        Args:
            section (str): The section name in the INI file.
            key (str): The key (option name) within the section.
            fallback: The value to return if the key is not found or not an integer.
                      Defaults to None.

        Returns:
            int | None: The configuration value as an integer, or the fallback value.

        Raises:
            ConfigurationError: If the value cannot be converted to an integer and
                                no fallback is provided that would prevent configparser's error.
        """
        try:
            return self.config.getint(section, key, fallback=fallback)
        except ValueError:
            # This occurs if the value exists but is not a valid integer.
            actual_value = self.config.get(section, key, fallback='<not found>')
            raise ConfigurationError(
                f"Value for '{key}' in [{section}] is not a valid integer. Found: '{actual_value}'"
            )

    def get_use_local_dns(self) -> int:
        """Returns the 'use_local_dns' setting (0 or 1)."""
        return self.get_int_setting('settings', 'use_local_dns')

    def get_use_external_dns(self) -> int:
        """Returns the 'use_external_dns' setting (0 or 1)."""
        return self.get_int_setting('settings', 'use_external_dns')

    def get_dns_servers_list(self) -> list[str]:
        """
        Returns a list of DNS server IP addresses to use for resolution.

        Combines "127.0.0.1" if 'use_local_dns' is 1, and servers from
        'dns_servers' if 'use_external_dns' is 1. Duplicates are removed.
        The order of servers might not be preserved due to set usage for deduplication.

        Returns:
            list[str]: A list of unique DNS server IP addresses.
        """
        dns_servers = []
        if self.get_use_local_dns() == 1:
            dns_servers.append("127.0.0.1")

        if self.get_use_external_dns() == 1:
            external_dns_str = self.get_setting('settings', 'dns_servers', '')
            if external_dns_str.strip(): # Ensure it's not empty before splitting
                 dns_servers.extend([server.strip() for server in external_dns_str.split(',')])
            # Validation (_validate_config) ensures 'dns_servers' is non-empty
            # if 'use_external_dns' is 1.
        return list(set(dns_servers)) # Remove duplicates.

    def get_domain_files(self) -> list[str]:
        """
        Returns a list of file paths containing domains to be processed.

        The paths are read from the 'domains_files' setting, which should be
        a comma-separated string of filenames.

        Returns:
            list[str]: A list of domain file paths.
        """
        domain_files_str = self.get_setting('settings', 'domains_files', '')
        # Validation (_validate_config) ensures this is a non-empty string.
        return [f.strip() for f in domain_files_str.split(',')]

    def get_output_file_path(self, name: str) -> str:
        """
        Returns the file path for the specified output file.

        Args:
            name (str): The key name of the output file setting (e.g.,
                        'output_domain_ip', 'output_only_ipv4').

        Returns:
            str: The file path for the specified output.
        """
        # Output files are read from the [settings] section.
        # Validation (_validate_config) ensures these exist and are non-empty.
        return self.get_setting('settings', name)

    def get_subnet_mask_value_for_network_calculation(self) -> str:
        """
        Returns the subnet mask value from config, intended for direct use with
        `ipaddress.IPv4Network(f'address/{value}')`.

        This value can be a prefix length (e.g., "24"), a full netmask string
        (e.g., "255.255.255.0"), or a CIDR prefix (e.g., "/24").
        Validation during initialization ensures this string is usable by
        `ipaddress.IPv4Network`.

        Returns:
            str: The subnet mask value as a string.
        """
        return self.get_setting('settings', 'subnet_mask', '')

    def get_subnet_mask_prefix(self) -> str:
        """
        Returns the subnet mask as a CIDR prefix string (e.g., "/24").

        This is primarily for display purposes or for systems that strictly
        require the '/' prefix. It converts various valid subnet mask formats
        (like "24" or "255.255.255.0") into the "/24" format.

        Returns:
            str: The subnet mask in CIDR prefix format (e.g., "/24").

        Raises:
            ConfigurationError: If the validated subnet_mask value cannot be
                                converted to prefix format, indicating an internal
                                validation logic inconsistency.
        """
        subnet_mask_value = self.get_subnet_mask_value_for_network_calculation()
        
        # If it already starts with '/', it's already in the desired CIDR prefix format.
        # Validation would have ensured it's a valid CIDR like "/24".
        if subnet_mask_value.startswith('/'):
            return subnet_mask_value
        
        # If it's a full mask (e.g., "255.255.255.0") or just digits (e.g., "24"),
        # convert it to a prefix length and then prepend '/'.
        try:
            # Create a temporary network object to derive the prefix length.
            # A dummy address part "0.0.0.0" is used for this conversion.
            network = ipaddress.ip_network(f"0.0.0.0/{subnet_mask_value}", strict=False)
            return f"/{network.prefixlen}"
        except ValueError:
            # This path should ideally not be reached if _validate_subnet_mask is effective,
            # as it implies that _validate_subnet_mask allowed a value that's not
            # convertible here. This would be an inconsistency in validation logic.
            raise ConfigurationError(
                f"Cannot convert validated subnet_mask ('{subnet_mask_value}') to prefix format. "
                "This indicates an issue with internal validation logic."
            )

if __name__ == '__main__':
    # This block is for example usage or standalone testing of this module.
    # It's not executed when the module is imported by other scripts.
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create a dummy config.ini for demonstration if this script is run directly.
    dummy_config_content = """
[settings]
use_local_dns = 0
use_external_dns = 1
dns_servers = 8.8.8.8, 1.1.1.1
domains_files = domains1.txt, domains2.txt
subnet_mask = 24
output_domain_ip = domain_ip_settings.txt
output_only_ipv4 = only_ipv4_settings.txt
output_keenetic = keenetic_settings.txt
"""
    try:
        with open('config.ini', 'w', encoding='utf-8') as f:
            f.write(dummy_config_content)
        
        app_config = AppConfig() # Test with the created dummy config
        logging.info(f"DNS Servers: {app_config.get_dns_servers_list()}")
        logging.info(f"Domain Files: {app_config.get_domain_files()}")
        logging.info(f"Output Domain IP: {app_config.get_output_file_path('output_domain_ip')}")
        logging.info(f"Output Only IPv4: {app_config.get_output_file_path('output_only_ipv4')}")
        logging.info(f"Output Keenetic: {app_config.get_output_file_path('output_keenetic')}")
        logging.info(f"Subnet Mask (value for calculation): {app_config.get_subnet_mask_value_for_network_calculation()}")
        logging.info(f"Subnet Mask (prefix for display): {app_config.get_subnet_mask_prefix()}")

    except ConfigurationError as e:
        logging.critical(f"Configuration Error during example run: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during example run: {e}")
    finally:
        # Clean up the dummy config.ini
        if os.path.exists('config.ini'):
            os.remove('config.ini')
            logging.debug("Dummy config.ini removed.")
