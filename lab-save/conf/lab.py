"""

lab_save v1.0 [20231120]

Script to repeat CLI commands over SSH

by Terence LEE <telee.hk@gmail.com>

https://github.com/telee0/admin_scripts
https://pexpect.readthedocs.io/en/stable/index.html

"""

cf = {
    'dgs': ['arista', 'cisco', 'ixia', 'nexus', 'pa'],  # order matters. ixia has nothing defined so will be skipped.

    'scp_host': '10.129.123.123',   # SCP host for config files, global setting
    'tftp_host': '10.129.123.123',  # TFTP host for config files, global setting

    'username': 'admin',         # sensitive and not exported, default admin
    'password': '',                 # sensitive and not exported, either here or through the env variable cf['passenv']
    'pass_env': 'PASS',             # name of the environment variable for the password

    'prompt': {                     # regex so prefixed with an 'r'
        'arista': [
            # r'.*assword:\s+',
            r'.*>',
            r'.*#',
        ],
        'cisco': [
            # r'.*Password:\s+',
            r'.*#',
        ],
        'nexus': [
            # r'.*Password:\s+',
            r'.*#\s+',
        ],
        'pa': [
            # r'.*Password:\s+',
            r'.*>\s+$',
            r'.*#\s+$',
        ],
    },

    'conn_timeout': 3,           # connection timeout
    'time_delay': 1,             # initial delay in seconds
    'cli_timeout': 10,           # > 0 or the cli will not expect a prompt

    'job_dir':  'job-{}',        # job folder
    'log_file': 'job-{}.log',    # job log
    'cnf_file': 'cnf-{}.json',   # config dump
    'cli_file': 'cli-{}.log',    # CLI output
    'sta_file': 'sta-{}.json',   # stats
    'log_buf_size': 99,          # log buffer size in message count

    'verbose': True,
    'debug': False,
}

# CLI tuples: (command_line, substitutions, timeout, new_prompt)
#

dg = 'arista'
if dg in cf['dgs']:
    cf.update({
        dg: {
            'scp_host': cf['scp_host'],        # SCP host for config files
            'tftp_host': cf['tftp_host'],      # TFTP host for config files
            'host_file': f"conf/{dg}.txt",     # list of devices
            'username': cf['username'],        # sensitive and not exported, default cf['admin']
            'password': cf['password'],        # sensitive and not exported, either here or through the env variable
            'pass_env': 'ARISTA_PASS',         # name of the environment variable for the password
            'time_delay': cf['time_delay'],    # initial delay in seconds
            'cli_timeout': cf['cli_timeout'],  # > 0 or the cli will not expect a prompt
            'cli': [
                'enable',
                ('terminal length 0', None, 0, cf['prompt'][dg][1],),
                'show clock',
                'show ver',
                ('copy running-config startup-config', None, 120,),
                ('copy running-config tftp://%s/%s', ['tftp_host', 'file'],),
                ('show clock', None, 10,),
                'exit',
            ]
        }
    })

dg = 'cisco'
if dg in cf['dgs']:
    cf.update({
        dg: {
            'scp_host': cf['scp_host'],        # SCP host for config files
            'tftp_host': cf['tftp_host'],      # TFTP host for config files
            'host_file': f"conf/{dg}.txt",     # list of devices
            'username': cf['username'],        # sensitive and not exported, default cf['admin']
            'password': cf['password'],        # sensitive and not exported, either here or through the env variable
            'pass_env': "CISCO_PASS",          # name of the environment variable for the password
            'time_delay': cf['time_delay'],    # initial delay in seconds
            'cli_timeout': cf['cli_timeout'],  # > 0 or the cli will not expect a prompt
            'cli': [
                'terminal length 0',
                'show clock',
                'show ver',
                # ('write', None, 300,),
                ('copy running-config startup-config', None, 0,), ('', None, 0,),  # just proceed without waiting
                ('copy running-config tftp://%s/%s', ['tftp_host', 'file'], 0), ('', None, 0,), ('', None, 0,),
                ('show clock', None, 10,),
                'exit',
            ]
        },
    })

dg = 'ixia'
if dg in cf['dgs']:
    cf.update({
        dg: None,
    })

dg = 'nexus'
if dg in cf['dgs']:
    cf.update({
        dg: {
            'scp_host': cf['scp_host'],        # SCP host for config files
            'tftp_host': cf['tftp_host'],      # TFTP host for config files
            'host_file': f"conf/{dg}.txt",     # list of devices
            'username': cf['username'],        # sensitive and not exported, default cf['admin']
            'password': cf['password'],        # sensitive and not exported, either here or through the env variable
            'pass_env': f"NEXUS_PASS",         # name of the environment variable for the password
            'time_delay': cf['time_delay'],    # initial delay in seconds
            'cli_timeout': cf['cli_timeout'],  #
            'cli': [
                'terminal length 0',
                'show clock',
                'show ver',
                ('copy running-config startup-config', None, 120),
                ('copy running-config tftp://%s/%s vrf management', ['tftp_host', 'file'],),
                ('show clock', None, 10,),
                'exit',
            ]
        },
    })

dg = 'pa'
if dg in cf['dgs']:
    cf.update({
        dg: {
            'scp_host': cf['scp_host'],        # SCP host for config files
            'tftp_host': cf['tftp_host'],      # TFTP host for config files
            'host_file': f"conf/{dg}.txt",     # list of devices
            'username': cf['username'],        # sensitive and not exported, default cf['admin']
            'password': cf['password'],        # sensitive and not exported, either here or through the env variable
            'pass_env': 'PA_PASS',             # name of the environment variable for the password
            'time_delay': cf['time_delay'],    #
            'cli_timeout': cf['cli_timeout'],  #
            'cli': [
                'show clock',
                'set cli pager off',
                'show system info',
                'configure',
                ('commit', None, 300, cf['prompt']['pa'][1],),
                ('save config to %s', ['file'],),
                'exit',
                ('show jobs all', None, 30, cf['prompt']['pa'][0]),
                ('tftp export configuration from %s to %s', ['file', 'tftp_host'],),
                'show clock',
                'exit',
            ]
        }
    })

# dictionary of search patterns for runtime metrics such as allocated sessions, packet rate, etc.
# These search patterns are regex for locating target numbers from output files
#
metrics = {
    #
    # Arista specific
    #
    'arista_serial_number':       (r'Serial number:\s+(\S+)', 'str'),
    #
    # Cisco specific
    #
    'cisco_model_number':         (r'Model Number:\s+(\S+)', 'str'),
    'cisco_serial_number':        (r'System Serial Number:\s+(\S+)', 'str'),
    #
    # Nexus specific
    #
    'nexus_device_name':         (r'Device name:\s+(\S+)', 'str'),
    #
    # PA specific
    #
    'pa_hostname':            (r'hostname:\s+(\S+)', 'str'),
    'pa_ip-address':          (r'ip-address:\s+(\S+)', 'str'),
    'pa_model':               (r'model:\s+(\S+)', 'str'),
    'pa_serial':              (r'serial:\s+(\S+)', 'str'),
    'pa_sw-version':          (r'sw-version:\s+(\S+)', 'str'),
    #
    # the following remain from the previous use cases
    #
    'activeTCPSessions':   r'active TCP sessions:\s+(\d+)',
    'activeUDPSessions':   r'active UDP sessions:\s+(\d+)',
    'allocatedSessions':   r'allocated sessions:\s+(\d+)',
    'connectionRate':      r'connection establish rate:\s+(\d+) cps',
    'eth1_1BytesReceived': r'bytes received\s+(\d+)',
    'packetRate':          r'Packet rate:\s+(\d+)\/s',
    'vpnIPSecTunnels':     r'Total (\d+) tunnels found',
    # 'test': r'abcde(\d)',
    # 'test': r'(\wa\w+)\s',
}

if __name__ == '__main__':
    pass
