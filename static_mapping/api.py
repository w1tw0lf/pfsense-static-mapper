import requests
import json # Import json for dummy response

class PfSenseAPI:
    def __init__(self, config):
        self.pfsense_ip = config.get('pfsense', 'ip')
        self.api_key = config.get('pfsense', 'api_key')
        self.interface = config.get('pfsense', 'interface')
        self.verify_ssl = config.getboolean('pfsense', 'verify_ssl')
        self.port = config.get('pfsense', 'port', fallback='') # Get port, default to empty string
        self.use_https = config.getboolean('pfsense', 'use_https', fallback=True)

        # Construct base URL with port if provided, and use /api/v2
        scheme = "https" if self.use_https else "http"
        if self.port:
            self.base_url = f"{scheme}://{self.pfsense_ip}:{self.port}/api/v2"
        else:
            self.base_url = f"{scheme}://{self.pfsense_ip}/api/v2"

    def _get_headers(self):
        """Returns common headers (like X-API-Key) for pfSense API authentication."""
        return {
            "X-API-Key": self.api_key,
            "Accept": "application/json"
        }

    def get_existing_static_mappings(self):
        """Retrieves existing static mappings for the configured interface."""
        # Using the endpoint confirmed by the user's working curl command
        url = f"{self.base_url}/services/dhcp_server?id={self.interface}"
        try:
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl)
            response.raise_for_status()
            json_response = response.json()
            data = json_response.get("data", {})
            static_maps = data.get("staticmap", []) # Assuming 'staticmap' is still the key
            return static_maps
        except requests.exceptions.RequestException as e:
            print(f"Error fetching existing static mappings: {e}")
            return []

    def create_static_mapping(self, mac_address, ip_address, hostname, description):
        """Creates a new static mapping."""
        # Endpoint for creating static mappings remains the same
        url = f"{self.base_url}/services/dhcp_server/static_mapping"
        payload = {
            "parent_id": self.interface,
            "mac": mac_address,
            "ipaddr": ip_address,
            "cid": hostname,
            "hostname": hostname,
            "domain": "",
            "domainsearchlist": [
                ""
            ],
            "defaultleasetime": 7200,
            "maxleasetime": 86400,
            "gateway": "",
            "dnsserver": [
                ""
            ],
            "winsserver": [
                ""
            ],
            "ntpserver": [
                ""
            ],
            "arp_table_static_entry": False,
            "descr": description
        }
        # Add Content-Type header specifically for POST requests
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"
        
        try:
            response = requests.post(url, headers=headers, json=payload, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating static mapping: {e}")
            return None

    def apply_changes(self):
        """Applies pending changes to the DHCP server."""
        url = f"{self.base_url}/services/dhcp_server/apply"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"
        try:
            response = requests.post(url, headers=headers, json={}, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error applying changes: {e}")
            return None

    