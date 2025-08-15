import json
from .api import PfSenseAPI
from .utils import find_next_available_ip
from .config import load_config

def create_static_mapping_entry(mac_address, hostname, description):
    """
    Core logic to create a static mapping entry in pfSense.
    Returns a tuple (success_status, message).
    """
    try:
        config = load_config()
        pfsense_api = PfSenseAPI(config)

        print("Fetching existing mappings...")
        existing_maps = pfsense_api.get_existing_static_mappings()

        print("Finding next available IP...")
        start_ip = config.get('ip_range', 'start')
        end_ip = config.get('ip_range', 'end')
        next_ip = find_next_available_ip(existing_maps, start_ip, end_ip)

        if next_ip:
            print(f"Next available IP: {next_ip}")
            print("Creating new static mapping...")
            result = pfsense_api.create_static_mapping(mac_address, next_ip, hostname, description)

            if result and result.get("status") == "ok":
                print("Static mapping created. Applying changes...")
                apply_result = pfsense_api.apply_changes()
                if apply_result and apply_result.get("status") == "ok":
                    message = "Static mapping created and changes applied successfully! 🎉"
                    return True, message
                else:
                    message = "Static mapping created, but failed to apply changes. Details:\n" + (json.dumps(apply_result, indent=2) if apply_result else "No response from apply API.")
                    return False, message
            else:
                message = "Failed to create static mapping. Details:\n" + (json.dumps(result, indent=2) if result else "No response from API.")
                return False, message
        else:
            message = "Could not find an available IP address in the specified range. 😢"
            return False, message

    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, f"An unexpected error occurred: {e}"