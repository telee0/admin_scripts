"""

lab_save v2.1 [20260619]
lab_save v2.0 [20260602]
lab_save v1.0 [20231120]

Script to repeat CLI commands over SSH

by Terence LEE <telee.hk@gmail.com>

https://github.com/telee0/admin_scripts
https://pexpect.readthedocs.io/en/stable/index.html

"""

cf = {
    'device_groups': ['pa'],
    # 'device_groups': ['arista', 'cisco', 'ixia', 'nexus', 'pa'],  # ixia has nothing defined so will be skipped

    'scp_host': '10.137.126.146',   # SCP host for config files, currently not used
    # 'tftp_host': '10.137.126.146',  # TFTP host for config files
    'tftp_host': '192.168.2.23',    # TFTP host for config files

    'username': 'pocadmin',         # sensitive and not exported, default admin
    'password': '',                 # sensitive and not exported, either here or through the env variable cf['passenv']
    'passenv': 'PASS',              # name of the environment variable for the password

    'priv_key': 'conf/id_rsa',      # private key for authentication
    'passphrase': '',               # passphrase

    'prompt': {                     # regex for the prompt
        'arista': [
            r'.*>',
            r'.*#',
        ],
        'cisco': [
            r'.*#',
        ],
        'nexus': [
            r'.*#\s+',
        ],
        'pa': [
            r'.*>\s+$',
            r'.*#\s+$',
        ],
    },

    'conn_timeout': 50,             # connection timeout
    'time_delay': 1,                # initial delay in seconds
    'cli_timeout': 10,              # > 0 or the cli will not expect a prompt
    'tty_size': (200, 40),          # terminal size for screenful CLI output capture

    'job_dir':  'job-{}',           # job folder
    'log_file': 'job-{}.log',       # job log
    'cnf_file': 'cf-{}.json',       # config dump
    'cli_file': 'cli-{}.log',       # CLI output
    'sta_file': 'sta-{}.json',      # stats
    'csv_file': 'dg-{}.csv',       # csv files
    'ctx_file': 'ctx-{}.json',      # runtime states

    'max_workers': 10,

    'version': '2.1',

    'verbose': True,
    'debug': False,
}

#
# Device specific configuration
#

cf.update({
    'arista': {
        'host_file': 'conf/arista.txt',
        'username': cf['username'],        # sensitive and not exported, default cf['admin']
        'password': cf['password'],        # sensitive and not exported, either here or through the env variable
        'passenv': 'ARISTA_PASS',         # name of the environment variable for the password
        'time_delay': cf['time_delay'],    # initial delay in seconds
        'cli_timeout': cf['cli_timeout'],  # > 0 or the cli will not expect a prompt
        'cli': [
            'enable',
            ('terminal length 0', 0, cf['prompt']['arista'][1]),
            'show clock',
            'show ver',
            ('copy running-config startup-config', 120),
            'copy running-config tftp://{tftp_host}/{file}',
            ('show clock', 10),
            'exit',
        ],
        'attrs': {
            'serial_number': r'Serial number:\s+(\S+)',
            'hardware': r'Arista\s+(\S+)',
            'software_version': r'Software image version:\s+(\S+)',
        }
    },

    'cisco': {
        'host_file': 'conf/cisco.txt',
        'username': cf['username'],        # sensitive and not exported, default cf['admin']
        'password': cf['password'],        # sensitive and not exported, either here or through the env variable
        'passenv': "CISCO_PASS",          # name of the environment variable for the password
        'time_delay': cf['time_delay'],    # initial delay in seconds
        'cli_timeout': cf['cli_timeout'],  # > 0 or the cli will not expect a prompt
        'cli': [
            'terminal length 0',
            'show clock',
            'show ver',
            # ('write', 300),
            ('copy running-config startup-config', 0,), ('', 0,),  # just proceed without waiting
            ('copy running-config tftp://{tftp_host}/{file}', 0), ('', 0), ('', 0),
            ('show clock', 10),
            'exit',
        ],
        'attrs': {
            'model_number': r'Model number\s+:\s+(\S+)',
            'serial_number': r'System serial number\s+:\s+(\S+)',
        }
    },

    'ixia': None,

    'nexus': {
        'host_file': 'conf/nexus.txt',
        'username': cf['username'],        # sensitive and not exported, default cf['admin']
        'password': cf['password'],        # sensitive and not exported, either here or through the env variable
        'passenv': f"NEXUS_PASS",         # name of the environment variable for the password
        'time_delay': cf['time_delay'],    # initial delay in seconds
        'cli_timeout': cf['cli_timeout'],  #
        'cli': [
            'terminal length 0',
            'show clock',
            'show ver',
            ('copy running-config startup-config', 120),
            'copy running-config tftp://{tftp_host}/{file} vrf management',
            ('show clock', 10),
            'exit',
        ],
        'attrs': {
            'device_name': r'Device name:\s+(\S+)',
            'hardware': r'cisco\s+\S+\s+(C\S+)\s+Chassis',
            'nxos': r'NXOS: version\s+(\S+)',
            'serial': r'Processor Board ID\s+(\S+)',
        }

    },

    'pa': {
        'host_file': 'conf/pa.txt',
        'username': cf['username'],        # sensitive and not exported, default cf['admin']
        'password': cf['password'],        # sensitive and not exported, either here or through the env variable
        'passenv': 'PA_PASS',             # name of the environment variable for the password
        'time_delay': cf['time_delay'],    #
        'cli_timeout': cf['cli_timeout'],  #
        'cli': [
            'show clock',
            'set cli pager off',
            'show system info',
            'configure',
            ('commit', 300, cf['prompt']['pa'][1]),
            'save config to {file}',
            'exit',
            ('show jobs all', 30, cf['prompt']['pa'][0]),
            'tftp export configuration from {file} to {tftp_host}',
            'show clock',
            'exit',
        ],
        'attrs': {
            'hostname': r'hostname:\s+(\S+)',
            'ip-address': r'ip-address:\s+(\S+)',
            'model': r'model:\s+(\S+)',
            'serial': r'serial:\s+(\S+)',
            'sw-version': r'sw-version:\s+(\S+)',
            'app-version': r'app-version:\s+(\S+)',
        }
    },
})


if __name__ == '__main__':
    pass
