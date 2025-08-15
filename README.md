# pfSense Static IP Mapper

This tool automates the process of adding new DHCP static IP mappings to a pfSense firewall using its API. It simplifies the management of static IP assignments by finding the next available IP address within a specified range and creating the mapping for a given MAC address, hostname, and description.

## Features

*   **pfSense API Integration:** Authenticates with the pfSense API using an API Key to manage static mappings.
*   **IP Address Management:** Retrieves existing static mappings for a specified interface and intelligently finds the next available IP address within a configurable range.
*   **Automated Mapping Creation:** Creates new static mappings with provided MAC address, hostname, and description.
*   **Dual Interface Support:** Provides a Web Interface for user-friendly management.
*   **Secure Web Interface:** Includes features like session-based authentication with hashed passwords, CSRF protection, and auto-logout for inactivity.
*   **Logging:** Comprehensive logging of application events, including login attempts and mapping operations.

## Setup

Follow these steps to get the project up and running:

1.  **pfSense API Setup:**

    This project relies on the `pfREST` API for pfSense. Follow these steps to set it up and generate an API key:

    *   **Install `pfREST`:**
        Connect to your pfSense firewall via SSH or console and run the following command:
        ```bash
        pkg install pfSense-pkg-restapi
        ```

    *   **Configure REST API:**
        Navigate to **System > REST API** in your pfSense webConfigurator.

    *   **Set Authentication Method:**
        Under **System > REST API > Settings**, set the **Authentication Methods** to `key`.

    *   **Add API Key:**
        Navigate to **System > REST API > Keys** and click on **Add Key**. Copy the generated key. This key will be used in your `config.ini` file.

    *   **Firewall Rules (if necessary):**
        If your pfSense firewall is not directly accessible from where you are running this application, you might need to add a firewall rule to allow access to the REST API port (default is 443 or 20443 if you changed it).

2.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd pfsense_static_mapper
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the application:**

    *   Rename `config.ini.example` to `config.ini`.
    *   Edit `config.ini` with your pfSense details and IP range.

    ```ini
    [pfsense]
    ip = YOUR_PFSENSE_IP
    api_key = YOUR_API_KEY
    interface = lan
    port = 443 # Optional: Specify the port if not 443 (e.g., 20443)
    verify_ssl = false # Set to true if you have a valid SSL certificate on your pfSense instance
    use_https = false # Set to true to use https, false to use http

    [ip_range]
    start = 192.168.1.10
    end = 192.168.1.99
    ```

    **Note on SSL Verification:** By default, `verify_ssl` is set to `false`. This is not recommended for production environments. If you have a proper certificate setup for your pfSense web interface, set this to `true`.

5.  **Web Interface Security Configuration:**

    The web interface includes several security features that require configuration:

    *   **FLASK_SECRET_KEY:** This is crucial for session security. Set it as an environment variable.
        ```bash
        # Generate a strong secret key
        python3 -c 'import secrets; print(secrets.token_hex(16))'

        # Set the environment variable (Linux/macOS)
        export FLASK_SECRET_KEY='your_generated_secret_key'

        # Set the environment variable (Windows PowerShell)
        $env:FLASK_SECRET_KEY='your_generated_secret_key'
        ```
        Replace `'your_generated_secret_key'` with the key you generated. For production, it is recommended to add this to your shell's startup file (e.g., `~/.bashrc`, `~/.zshrc`) or use a `.env` file.

    *   **Authentication Credentials:** The web interface uses a username and a hashed password for authentication. Configure these in your `config.ini` file under the `[auth]` section.

        ```bash
        # Generate a password hash
        python3 hash_password.py 'your_password_here'
        ```
        Copy the generated hash and paste it into the `password_hash` field in your `config.ini` file. You can also change the `username`.

        ```ini
        [auth]
        username = admin
        password_hash = your_generated_password_hash
        ```

## Usage

This tool can be used via a Web Interface.

### Web Interface

To run the web interface, use the following command from the project root directory:

```bash
python web_run.py
```

This will start a Gunicorn server on `http://0.0.0.0:8000`.

Once the server is running, open your web browser and navigate to the address displayed in your terminal.

On the web page, you can enter the following:

*   **Name:** The first name of the user/device.
*   **Surname:** The last name of the user/device.
*   **MAC Address:** The MAC address of the device.

The web interface will automatically generate the `hostname` as `name-surname` (e.g., `john-doe`) and the `description` as `Name Surname` (e.g., `John Doe`).

## Production Deployment

While `python web_run.py` is a convenient way to start the server, for more advanced production deployments, you can run Gunicorn directly. This allows for more configuration options.

For example, to run the application with 4 worker processes, you can use the following command:

```bash
gunicorn --workers 4 --bind 0.0.0.0:8000 wsgi:app
```

For more information on Gunicorn configuration, please refer to the [Gunicorn documentation](https://gunicorn.org/).