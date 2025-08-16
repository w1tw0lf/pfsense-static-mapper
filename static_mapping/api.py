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

    def get_existing_static_mappings(self, interface=None):
        if not interface:
            interface = self.interface
        url = f"{self.base_url}/services/dhcp_server?id={interface}"
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

    def get_interface_details(self, interface=None):
        if not interface:
            interface = self.interface
        url = f"{self.base_url}/interface?id={interface}"
        try:
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl)
            response.raise_for_status()
            json_response = response.json()
            data = json_response.get("data", {})
            ip_address = data.get("ipaddr")
            subnet = data.get("subnet")
            description = data.get("descr")
            return ip_address, subnet, description
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting interface details: {e}")
            raise e

    def get_dhcp_range(self, interface=None):
        if not interface:
            interface = self.interface
        url = f"{self.base_url}/services/dhcp_server?id={interface}"
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

    def create_static_mapping(self, interface, mac_address, ip_address, hostname, description):
        url = f"{self.base_url}/services/dhcp_server/static_mapping"
        payload = {
            "parent_id": interface,
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

    def get_available_interfaces(self):
        url = f"{self.base_url}/interface/available_interfaces?limit=0&offset=0"
        try:
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl)
            response.raise_for_status()
            json_response = response.json()
            return json_response.get("data", [])
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting available interfaces: {e}")
            raise e

    def get_dhcp_server_interfaces(self):
        available_interfaces = self.get_available_interfaces()
        dhcp_interfaces = []
        for iface in available_interfaces:
            interface_id = iface.get('in_use_by')
            if not interface_id:
                continue

            url = f"{self.base_url}/services/dhcp_server?id={interface_id}"
            try:
                response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl)
                if response.status_code == 200:
                    json_response = response.json()
                    data = json_response.get("data", {})
                    if data.get('enable'):
                        dhcp_interfaces.append(interface_id)
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error checking DHCP server for interface {interface_id}: {e}")
        return dhcp_interfaces
