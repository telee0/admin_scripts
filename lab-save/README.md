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
'max_workers': 50
