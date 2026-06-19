# What is lab-save ?

A Python-based lab administration tool designed to automate common network operational tasks across multiple devices:

- Configuration backup and export: Automates saving device configurations and transferring them to remote destinations such as SCP servers or TFTP repositories.
- Device inventory collection: Extracts and aggregates key device attributes from CLI outputs, including hardware model, serial number, and operating system version, to build a structured inventory.
- Configuration standardization: Applies consistent settings across devices, such as DNS servers, Panorama management IPs, and hostnames.
- Parallel execution support: Enables efficient bulk device operations through concurrent processing using Python ThreadPoolExecutor.
- Support a variety of device types, including Arista switches, Catalyst switches, Nexus switches, PAN-OS devices (NGFW and Panorama)

The tool consists of the following set of files.

- lab-save.py	- main script
- conf/lab.py	- configuration file
- conf/*.txt		- device lists, each belonging to a device type with applicable configuration

### Parallel execution support

This configuration key controls the concurrency setting by allowing a larger pool of threads to interact with target devices. Set this large enough for the script to complete the tasks more quickly.

<pre>
  
'max_workers': 50

</pre>

### Device lists

Device IPs are organized by device type.

The # character is used for comments; any content after # on a line is ignored by the script.

Device-specific settings—such as CLI commands and regex patterns used to extract attributes from CLI output—apply only within their respective device group.

Access credentials are managed as follows:
- The login username provided via the command-line argument (-u) is shared across all devices by default.
- If different usernames are required per device type, they can be defined in the configuration file using the username key within each device group block.
- Passwords are shared within a device group and should be supplied via environment variables for security reasons. The corresponding environment variable name is defined in the configuration file using the passenv key.

Ensure that all required access credentials are properly configured on the target devices prior to execution. For security purposes, contact the script maintainer to obtain or verify the required credentials.

### Public key authenticaton

- New scripts will support public key authentication.
- They can authenticate either with username/password or username/private key
- All devices of the same device group share the same username/password and username/key pair. 
- If the public key has not yet been deployed on a device, the scripts will fall back to authenticate with username/password. 
- If the key pair (path to private key) has not been specified at the group level configuration, the one at the top level is assumed.
- key pair can be generated with openssl. The private key can be put in a subfolder of the script.
