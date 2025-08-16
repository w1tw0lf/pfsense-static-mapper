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

    # Get existing mappings and DHCP range for available IP count
    existing_maps = pfsense_api.get_existing_static_mappings()
    interface_ip, interface_subnet = pfsense_api.get_interface_details()
    dhcp_range_from, dhcp_range_to = pfsense_api.get_dhcp_range()

    available_ips_count = 0
    if interface_ip and interface_subnet and dhcp_range_from and dhcp_range_to:
        available_ips_count = count_available_ips(existing_maps, interface_ip, interface_subnet, dhcp_range_from, dhcp_range_to)

    if form.validate_on_submit():
        hostname = form.hostname.data
        description = form.description.data
        mac_address = form.mac_address.data

        success, message, _ = create_static_mapping_entry(mac_address, hostname, description, current_app.logger)

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