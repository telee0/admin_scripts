"""

lab_save v2.0 [20260602]
lab_save v1.0 [20231120]

Script to repeat CLI commands over SSH

by Terence LEE <telee.hk@gmail.com>

https://github.com/telee0/admin_scripts
https://github.com/fgimian/paramiko-expect/blob/master/examples/paramiko_expect-demo.py

"""

import argparse
import importlib.util
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from os import makedirs
from os.path import exists

import pandas as pd
import paramiko
from paramiko_expect import SSHClientInteraction

ctx = {  # context to store runtime data
    'start_time': datetime.now(),
}


def get_logger(name, log_file):
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '[%(asctime)s] %(threadName)s %(funcName)s %(levelname)s %(message)s'
    )

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger


def init():
    print(ctx['args'], "\n")

    ctx['verbose'] = cf['verbose'] or ctx['args'].verbose
    ctx['debug'] = cf['debug']

    start_time = ctx['start_time']
    ddhhmm = start_time.strftime('%d%H%M')

    for f in ('job_dir', 'cnf_file', 'sta_file', 'log_file', 'ctx_file'):
        ctx[f] = cf[f].format(ddhhmm) if f in cf else f"{f}-{ddhhmm}"

    job_dir = ctx['job_dir']
    makedirs(job_dir, exist_ok=True)

    ctx['log'] = get_logger(__name__, os.path.join(job_dir, ctx['log_file']))
    ctx['log'].setLevel(logging.DEBUG if ctx['debug'] else logging.INFO if ctx['verbose'] else logging.WARNING)

    ctx['log'].info(f"initializing the environment..")

    ctx['yyyymmdd'] = start_time.strftime('%Y%m%d')

    ctx['device_groups'] = []
    ctx['hosts'] = {}

    u, p, e = 'username', 'password', 'passenv'
    x = (u, p)
    y = ('admin', None)  # default

    for dg in cf['device_groups']:
        if dg not in cf or cf[dg] is None:
            ctx['log'].warning(f"dg = {dg}: device group undefined or skipped..")
            continue
        ctx[dg] = {'hosts': [], 'ext': ('xml' if dg =='pa' else 'txt')}
        z = (ctx['args'].user, os.getenv(cf[dg][e]))  # specified through CLI
        for i, attr in enumerate(x):
            ctx[dg][attr] = z[i] or cf[dg][attr] or cf[attr] or y[i]
            val = ctx[dg][attr]
            if not val:
                ctx['log'].error(f"access undefined or empty")
                ctx['log'].error(f"check {ctx['args'].conf} for details ({dg}.{attr})")
                sys.exit(1)
            if ctx['verbose']:
                print(f"\tdg = {dg}, attr = {attr}, val = {val}")  # do not log credentials
        try:
            with open(cf[dg]['host_file'], "r", encoding="ascii") as f:
                for line_num, line in enumerate(f):
                    host = line.split("#", 1)[0].strip()
                    if host:
                        if host in ctx['hosts']:
                            ctx['log'].warning(f"host {host} already found in {ctx['hosts'][host]['dg']}..")
                            continue
                        ctx['hosts'][host] = {
                            'dg': dg,
                            'cli_file': cf['cli_file'].format(host)  # f"{host}-{ddhhmm}"),
                        }
                        ctx[dg]['hosts'].append(host)
        except Exception as e:
            ctx['log'].error(f"{str(e)}")
            sys.exit(1)
        if len(ctx[dg]['hosts']) > 0:
            ctx['device_groups'].append(dg)

    os.chdir(job_dir)

    ctx['log'].info("verbose = %s, debug = %s", ctx['verbose'], ctx['debug'])


def send_cli(interact, params):
    output = []

    dg = params['dg']
    seq = params['seq']
    cli = cf[dg]['cli']
    timeout = cf[dg]['cli_timeout']
    prompt = cf['prompt'][dg][0]

    n = len(cli)
    for i, c in enumerate(cli, start=1):
        ctx['log'].info(f"[{seq}_{i:02d}/{n}] c = {c}")

        c_ = (c,) if isinstance(c, str) else c  # convert it back to a tuple in case of a string
        c_len = len(c_)

        command = c_[0].format(**params)
        timeout = c_[1] if c_len > 1 else timeout  # c_: cli tuple: (command, timeout, prompt_new)
        prompt  = c_[2] if c_len > 2 else prompt

        if timeout > 0:
            interact.expect([prompt], timeout=timeout)
        interact.send(command)

        o = interact.current_output_clean
        o = o.replace('\x00', '')                                # remove NUL characters
        o = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', o)  # remove ANSI escape sequences
        output.append(o)

    return output


def collect_data(host, dg, seq):
    output = {'host': host, 'seq': seq}

    client = None

    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=host,
            username=ctx[dg]['username'], password=ctx[dg]['password'],
            timeout=cf['conn_timeout']
        )
    except Exception as e:
        ctx['log'].warning(f"host {host}: {str(e)}")
        client.close()
        output['close_time'] = datetime.now()
        return output

    output['connect_time'] = datetime.now()
    ctx['log'].info(f"SSH connected to {host} ({seq}) as {ctx[dg]['username']}..")

    time_delay = max(0, cf.get(dg, {}).get('time_delay', cf['time_delay']))

    try:
        with SSHClientInteraction(
                client, timeout=10, display=ctx['debug'],
                tty_width=cf['tty_size'][0], tty_height=cf['tty_size'][1]
        ) as interact:
            ctx['log'].info(f"sleep for {time_delay} seconds..")
            time.sleep(time_delay)  # wait for at least 3 seconds
            interact.send("\n")
            t = datetime.now()
            params = {
                'dg': dg,
                'file': f"{dg}-{host}-{ctx['yyyymmdd']}.{ctx[dg]['ext']}",  # config to be saved as
                'scp_host': cf['scp_host'],
                'tftp_host': cf['tftp_host'],
                'seq': seq,
            }
            output['data'] = send_cli(interact, params)
            ctx['log'].info(f"execution time for host {host}: {datetime.now() - t}")
    except Exception as e:
        ctx['log'].warning(f"host {host}: {str(e)}")
    finally:
        client.close()
        output['close_time'] = datetime.now()

    if 'data' in output:
        file = ctx['hosts'][host]['cli_file']  # .format(ddhhmm)
        with open(file, 'a') as f:
            f.write("\n".join(output['data']))
            ctx['log'].info("%s saved", file)

    return output


def lab_save():
    tasks = []
    seq = 1
    for dg in ctx['device_groups']:
        hosts = ctx[dg]['hosts']
        for i, host in enumerate(hosts, start=1):
            # ctx['log'].info(f"[{i:02d}/{n}] dg {dg} host {host}..")
            # output[host] = collect_data(host, dg)
            tasks.append((host, dg, seq))
            seq += 1

    with ThreadPoolExecutor(max_workers=cf['max_workers']) as executor:
        results = executor.map(lambda x: collect_data(*x), tasks)

    output = {o['host']: o for o in results}

    return output


def write_files(data, stats=None):
    ctx['log'].info(f"generating output at {ctx['job_dir']}/..")

    file = ctx['cnf_file']
    with open(file, 'a') as f:
        cred = [(cf['username'], cf['password'])]
        del cf['username'], cf['password']
        key_list = []
        for key in cf.keys():
            if isinstance(cf[key], dict) and 'username' in cf[key]:
                cred.append((cf[key]['username'], cf[key]['password']))
                del cf[key]['username'], cf[key]['password']
                key_list.append(key)
        f.write(json.dumps({'cf': cf}, indent=2))
        cf['username'], cf['password'] = cred[0]
        for i, key in enumerate(key_list, start=1):
            cf[key]['username'], cf[key]['password'] = cred[i]
        ctx['log'].info(f"{file} saved")

    # cli response files are written individually so not here

    if stats is not None:
        file = ctx['sta_file']
        with open(file, 'a') as f:
            f.write(json.dumps(stats, indent=2))
            ctx['log'].info(f"{file} saved")

    inventory = {}
    for dg in ctx['device_groups']:
        inventory[dg] = {}
    for host, attrs in stats.items():
        dg = ctx['hosts'][host]['dg']
        inventory[dg][host] = attrs
    for dg in ctx['device_groups']:
        if inventory[dg]:
            df = pd.DataFrame.from_dict(inventory[dg], orient='index')
            df.to_csv(cf['csv_file'].format(dg), index=False)


def get_joke():
    try:
        import pyjokes
        print(f"\n{pyjokes.get_joke()}")
    except Exception:
        pass


def cleanup():
    ctx['log'].info(f"cleaning up..")

    for dg in ctx['device_groups']:
        del ctx[dg]['username'], ctx[dg]['password']

    ctx['end_time'] = datetime.now()
    ctx['log'].info(f"total execution time for all hosts: %s", ctx['end_time'] - ctx['start_time'])

    get_joke()

    file = ctx['ctx_file']
    for key, val in ctx.items():
        if isinstance(val, dict):
            for k, v in val.items():
                if isinstance(v, set):
                    val[k] = list(v)
        elif isinstance(val, list):
            ctx[key] = [v.isoformat() if isinstance(v, datetime) else v for v in val]
        elif isinstance(val, datetime):
            ctx[key] = val.isoformat()
    with open(file, "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2,
            skipkeys=True,
            default=lambda o: '<not serializable>',
        )


def analyze(data):
    ctx['log'].info(f"analyzing data..")

    results = {}  # results extracted from data

    for host in data.keys():
        if 'data' not in data[host]:
            continue
        dg = ctx['hosts'][host]['dg']
        results[host] = {}
        for attr, pat_list in cf[dg]['attrs'].items():
            pattern = pat_list[0] if isinstance(pat_list, tuple) else pat_list
            for i, text in enumerate(data[host]['data']):
                match = re.search(pattern, text)
                if match:
                    values = list(match.groups())
                    if attr not in results[host]:
                        results[host][attr] = []
                    results[host][attr].append(values)
                    ctx['log'].info(f"host {host}, attr {attr}, values: {values}")
                ctx['log'].debug(f"{i} - text = {text}")
                ctx['log'].debug("-" * 80)
            if attr in results[host]:
                results[host][attr] = results[host][attr][0][0]

    return results


def read_conf(cf_path):
    if not exists(cf_path):
        print(f"{cf_path}: file not found", file=sys.stderr)
        sys.exit(1)
    name = "conf"
    spec = importlib.util.spec_from_file_location(name, cf_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='lab-save.py', description='Script to save device config.', add_help=False)
    parser.add_argument('-c', '--conf', nargs='?', type=str, default="conf/lab.py", help="config file")
    parser.add_argument('-u', '--user', type=str, help="user")
    parser.add_argument('-v', '--verbose', action='store_true', help="verbose mode")
    parser.add_argument('-?', '--help', action='help', help='show this help message and exit')
    parser.print_help()
    print()

    ctx['args'] = parser.parse_args()

    read_conf(ctx['args'].conf)
    from conf import cf

    init()
    data_ = lab_save()
    stats_ = analyze(data_)
    write_files(data_, stats_)
    cleanup()
