import requests
import json
import logging

class PfSenseAPI:
    def __init__(self, config, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.pfsense_ip = config.get('pfsense', 'ip')
        self.api_key = config.get('pfsense', 'api_key')
        self.interface = config.get('pfsense', 'interface')
        self.verify_ssl = config.getboolean('pfsense', 'verify_ssl')
        self.port = config.get('pfsense', 'port', fallback='')
        self.use_https = config.getboolean('pfsense', 'use_https', fallback=True)

        scheme = "https" if self.use_https else "http"
        if self.port:
            self.base_url = f"{scheme}://{self.pfsense_ip}:{self.port}/api/v2"
        else:
            self.base_url = f"{scheme}://{self.pfsense_ip}/api/v2"

    def _get_headers(self):
        return {
            "X-API-Key": self.api_key,
            "Accept": "application/json"
        }

    def get_existing_static_mappings(self):
        url = f"{self.base_url}/services/dhcp_server?id={self.interface}"
        try:
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl)
            response.raise_for_status()
            json_response = response.json()
            data = json_response.get("data", {})
            static_maps = data.get("staticmap", [])
            return static_maps
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting existing static mappings: {e}")
            raise e

    def get_interface_details(self):
        url = f"{self.base_url}/interface?id={self.interface}"
        try:
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl)
            response.raise_for_status()
            json_response = response.json()
            data = json_response.get("data", {})
            ip_address = data.get("ipaddr")
            subnet = data.get("subnet")
            return ip_address, subnet
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting interface details: {e}")
            raise e

    def get_dhcp_range(self):
        url = f"{self.base_url}/services/dhcp_server?id={self.interface}"
        try:
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl)
            response.raise_for_status()
            json_response = response.json()
            data = json_response.get("data", {})
            range_from = data.get("range_from")
            range_to = data.get("range_to")
            return range_from, range_to
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting DHCP range: {e}")
            raise e

    def create_static_mapping(self, mac_address, ip_address, hostname, description):
        url = f"{self.base_url}/services/dhcp_server/static_mapping"
        payload = {
            "parent_id": self.interface,
            "mac": mac_address,
            "ipaddr": ip_address,
            "cid": hostname,
            "hostname": hostname,
            "domain": "",
            "domainsearchlist": [""],
            "defaultleasetime": 7200,
            "maxleasetime": 86400,
            "gateway": "",
            "dnsserver": [""],
            "winsserver": [""],
            "ntpserver": [""],
            "arp_table_static_entry": False,
            "descr": description
        }
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"
        
        try:
            response = requests.post(url, headers=headers, json=payload, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error creating static mapping: {e}")
            raise e

    def apply_changes(self):
        url = f"{self.base_url}/services/dhcp_server/apply"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"
        try:
            response = requests.post(url, headers=headers, json={}, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error applying changes: {e}")
            raise e