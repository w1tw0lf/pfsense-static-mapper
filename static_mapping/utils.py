import ipaddress

def find_next_available_ip(existing_mappings, start_ip, end_ip):
    """Finds the next available IP in the specified range."""
    
    # Parse IP range
    start_ip_obj = ipaddress.IPv4Address(start_ip)
    end_ip_obj = ipaddress.IPv4Address(end_ip)

    # Extract currently used IPs from mappings
    used_ips = {mapping.get("ipaddr") for mapping in existing_mappings if mapping.get("ipaddr")}

    # Iterate through the range to find the first unused IP
    current_ip = start_ip_obj
    while current_ip <= end_ip_obj:
        if str(current_ip) not in used_ips:
            return str(current_ip)
        current_ip += 1
    return None # No available IP found