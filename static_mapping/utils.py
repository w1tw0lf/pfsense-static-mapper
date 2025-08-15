import ipaddress

def find_next_available_ip(existing_mappings, interface_ip, interface_subnet, dhcp_range_from, dhcp_range_to):
    """Finds the next available IP outside the DHCP range but within the network range."""
    
    try:
        network = ipaddress.ip_network(f"{interface_ip}/{interface_subnet}", strict=False)
        dhcp_start_ip = ipaddress.IPv4Address(dhcp_range_from)
        dhcp_end_ip = ipaddress.IPv4Address(dhcp_range_to)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError) as e:
        print(f"Error parsing IP addresses or subnet in find_next_available_ip: {e}")
        return None

    # Extract currently used IPs from mappings
    used_ips = {mapping.get("ipaddr") for mapping in existing_mappings if mapping.get("ipaddr")}
    used_ips.add(interface_ip) # Exclude the interface IP itself

    # Iterate through the network's usable hosts
    for ip_obj in network.hosts():
        # Check if IP is outside the DHCP range and not already used
        if (ip_obj < dhcp_start_ip or ip_obj > dhcp_end_ip) and str(ip_obj) not in used_ips:
            return str(ip_obj)

    return None # No available IP found

def count_available_ips(existing_mappings, interface_ip, interface_subnet, dhcp_range_from, dhcp_range_to):
    """Counts the number of available IPs outside the DHCP range but within the network range."""
    try:
        network = ipaddress.ip_network(f"{interface_ip}/{interface_subnet}", strict=False)
        dhcp_start_ip = ipaddress.IPv4Address(dhcp_range_from)
        dhcp_end_ip = ipaddress.IPv4Address(dhcp_range_to)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError) as e:
        print(f"Error parsing IP addresses or subnet in count_available_ips: {e}")
        return 0

    used_ips = {mapping.get("ipaddr") for mapping in existing_mappings if mapping.get("ipaddr")}
    used_ips.add(interface_ip) # Exclude the interface IP itself
    available_count = 0

    for ip_obj in network.hosts():
        if (ip_obj < dhcp_start_ip or ip_obj > dhcp_end_ip) and str(ip_obj) not in used_ips:
            available_count += 1

    return available_count