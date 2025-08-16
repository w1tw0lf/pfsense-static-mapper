import json
from .api import PfSenseAPI
from .utils import find_next_available_ip, count_available_ips
from .config import load_config

def create_static_mapping_entry(interface, mac_address, hostname, description, logger):
    """
    Core logic to create a static mapping entry in pfSense.
    Returns a tuple (success_status, message, available_ips_count).
    """
    try:
        config = load_config()
        pfsense_api = PfSenseAPI(config, logger)

        # Check for duplicate hostname or MAC address
        existing_maps = pfsense_api.get_existing_static_mappings(interface)
        for existing_map in existing_maps:
            if existing_map.get('hostname') == hostname:
                return False, f'Error: Hostname \'{hostname}\' already exists.', None
            if existing_map.get('mac') == mac_address:
                return False, f'Error: MAC Address \'{mac_address}\' already exists.', None

        interface_ip, interface_subnet, _ = pfsense_api.get_interface_details(interface)

        dhcp_range_from, dhcp_range_to = pfsense_api.get_dhcp_range(interface)

        next_ip = find_next_available_ip(existing_maps, interface_ip, interface_subnet, dhcp_range_from, dhcp_range_to)

        if next_ip:
            result = pfsense_api.create_static_mapping(interface, mac_address, next_ip, hostname, description)

            if result and result.get("status") == "ok":
                apply_result = pfsense_api.apply_changes()
                if apply_result and apply_result.get("status") == "ok":
                    logger.info(f"Static mapping created for MAC {mac_address} on interface {interface} with IP {next_ip}")
                    message = "Static mapping created and changes applied successfully! 🎉"
                    available_ips_count = count_available_ips(existing_maps, interface_ip, interface_subnet, dhcp_range_from, dhcp_range_to)
                    return True, message, available_ips_count
                else:
                    message = "Static mapping created, but failed to apply changes. Details:\n" + (json.dumps(apply_result, indent=2) if apply_result else "No response from apply API.")
                    logger.error(f"Failed to apply changes: {message}")
                    return False, message, None
            else:
                message = "Failed to create static mapping. Details:\n" + (json.dumps(result, indent=2) if result else "No response from API.")
                logger.error(f"Failed to create static mapping: {message}")
                return False, message, None
        else:
            message = "Could not find an available IP address in the specified range. 😢"
            return False, message, None

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False, f"An unexpected error occurred: {e}", None