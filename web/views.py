import configparser
from flask import Blueprint, render_template, request, redirect, url_for, flash, get_flashed_messages, session, current_app
from web.forms import MappingForm
from static_mapping.core import create_static_mapping_entry
from static_mapping.utils import count_available_ips
from static_mapping.api import PfSenseAPI
from web.auth import login_required

views_bp = Blueprint('views', __name__)

@views_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = MappingForm()

    # Load config for PfSenseAPI initialization
    pfsense_config = configparser.ConfigParser()
    pfsense_config.read('config.ini')

    # Initialize PfSenseAPI
    pfsense_api = PfSenseAPI(pfsense_config, current_app.logger)

    # Get interfaces with DHCP server enabled
    dhcp_interfaces = pfsense_api.get_dhcp_server_interfaces()
    current_app.logger.info(f"DHCP interfaces: {dhcp_interfaces}")
    available_interfaces = pfsense_api.get_available_interfaces()
    

    # Filter available interfaces to only include those with DHCP server enabled
    interfaces_with_dhcp = [iface for iface in available_interfaces if iface['in_use_by'] in dhcp_interfaces]
    

    # Get subnet for each interface and create choices for the form
    interface_choices = []
    for iface in interfaces_with_dhcp:
        ip_address, subnet, description = pfsense_api.get_interface_details(iface['in_use_by'])
        if ip_address and subnet:
            interface_choices.append((iface['in_use_by'], f"{description} ({ip_address}/{subnet})"))

    form.interface.choices = interface_choices

    # Set default interface if not a POST request or if form validation fails
    if not form.is_submitted() or not form.validate():
        if interface_choices:
            form.interface.data = interface_choices[0][0]

    # Get existing mappings and DHCP range for available IP count
    if request.method == 'POST' and form.validate_on_submit():
        selected_interface = form.interface.data
        existing_maps = pfsense_api.get_existing_static_mappings(selected_interface)
        interface_ip, interface_subnet, _ = pfsense_api.get_interface_details(selected_interface)
        dhcp_range_from, dhcp_range_to = pfsense_api.get_dhcp_range(selected_interface)
    else:
        # For GET request, show available IPs for the first interface in the list
        if interface_choices:
            first_interface = interface_choices[0][0]
            existing_maps = pfsense_api.get_existing_static_mappings(first_interface)
            interface_ip, interface_subnet, _ = pfsense_api.get_interface_details(first_interface)
            dhcp_range_from, dhcp_range_to = pfsense_api.get_dhcp_range(first_interface)
        else:
            existing_maps = []
            interface_ip, interface_subnet, dhcp_range_from, dhcp_range_to = None, None, None, None

    available_ips_count = 0
    if interface_ip and interface_subnet and dhcp_range_from and dhcp_range_to:
        available_ips_count = count_available_ips(existing_maps, interface_ip, interface_subnet, dhcp_range_from, dhcp_range_to)

    if form.validate_on_submit():
        interface = form.interface.data
        hostname = form.hostname.data
        description = form.description.data
        mac_address = form.mac_address.data

        success, message, _ = create_static_mapping_entry(interface, mac_address, hostname, description, current_app.logger)

        if success:
            flash(message, 'success')
            current_app.logger.info(f"User '{session.get('username')}' created a new static mapping for MAC address '{mac_address}'.")
        else:
            flash(message, 'error')
            current_app.logger.error(f"Failed to create static mapping for MAC address '{mac_address}'. Reason: {message}")
        return redirect(url_for('views.index'))

    messages = get_flashed_messages(with_categories=True)
    success_flag = False
    for category, message in messages:
        if category == 'success':
            success_flag = True
            break
            
    return render_template('index.html', form=form, messages=messages, success_flag=success_flag, available_ips_count=available_ips_count)

@views_bp.route('/get_available_ips/<interface>')
@login_required
def get_available_ips(interface):
    pfsense_config = configparser.ConfigParser()
    pfsense_config.read('config.ini')
    pfsense_api = PfSenseAPI(pfsense_config, current_app.logger)

    existing_maps = pfsense_api.get_existing_static_mappings(interface)
    interface_ip, interface_subnet, _ = pfsense_api.get_interface_details(interface)
    dhcp_range_from, dhcp_range_to = pfsense_api.get_dhcp_range(interface)

    available_ips_count = 0
    if interface_ip and interface_subnet and dhcp_range_from and dhcp_range_to:
        available_ips_count = count_available_ips(existing_maps, interface_ip, interface_subnet, dhcp_range_from, dhcp_range_to)

    return str(available_ips_count)
