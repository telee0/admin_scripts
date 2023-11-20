"""

lab_save v1.0 [20231120]

Script to repeat CLI commands over SSH

by Terence LEE <telee.hk@gmail.com>

https://github.com/telee0/admin_scripts
https://pexpect.readthedocs.io/en/stable/index.html

"""

import argparse
import importlib.util
import json
import os
import re
import sys
import time
from datetime import datetime
from os import makedirs
from os.path import exists

import paramiko
from paramiko_expect import SSHClientInteraction

# from cli import cf, cli, metrics

verbose, debug = True, False
step = 0
log_buf = []


def init():
    global step
    global args
    global verbose, debug

    func = "init"

    step = 0

    verbose = (cf['verbose'] and args.verbose) if 'verbose' in cf else verbose
    debug = cf['debug'] if 'debug' in cf else debug

    print(f"-- initialize the environment..")

    u, p, e = 'username', 'password', 'pass_env'

    dgs, count = [], 0

    for dg in cf['dgs']:
        if cf[dg] is None:
            print(f"** {func}: dg = {dg}: device group undefined and skipped")
            count += 1
            continue
        dgs.append(dg)
        if u not in cf[dg] or len(cf[dg][u]) <= 0:
            cf[dg][u] = 'admin'  # default 'admin'
        if p not in cf[dg] or len(cf[dg][p]) <= 0:
            cf[dg][p] = os.getenv(cf[dg][e]) if e in cf[dg] else None  # password from the env variable
        if cf[dg][p] is None or len(cf[dg][p]) <= 0:
            print("init: {0}: access not specified or empty".format(dg))
            print("init: check {0} for details ('{1}')".format(args.conf, e))
            exit(1)

    if count > 0:
        cf['dgs'] = dgs

    t = datetime.now().strftime('%Y%m%d%H%M')
    ddhhmm = t[6:12]

    job_files = ['job_dir', 'cnf_file', 'cli_file', 'sta_file', 'log_file']
    for f in job_files:
        if f not in cf:
            cf[f] = f
        else:
            cf[f] = cf[f].format(ddhhmm)

    # prepare the directory structure for job files
    #
    job_dir = cf['job_dir']  # .format(ddhhmm)
    makedirs(job_dir, exist_ok=True)
    for f in job_files[1:]:
        cf[f] = job_dir + '/' + cf[f]

    log("[{0:02.2f}] verbose = {1}, debug = {2}".format(step, verbose, debug))


def log(message, flush=False):
    global log_buf

    t = datetime.now().strftime('%H:%M:%S')
    message = f"[{t}] " + message
    log_buf.append(message)
    # print("message:", message)
    if len(log_buf) > cf['log_buf_size'] or flush:
        with open(cf['log_file'], 'a') as f:
            f.write("\n".join(log_buf))
        log_buf.clear()
        if len(log_buf) > 0:
            print(f"log: entries not written to {cf['log_file']}")
            exit(1)


# check here for more use cases
#
# https://github.com/fgimian/paramiko-expect/blob/master/examples/paramiko_expect-demo.py

def send_cli(interact, params):
    global step

    func = "send_cli"

    output = []

    dg = params['dg']
    cli = cf[dg]['cli']
    timeout = cf[dg]['cli_timeout']
    prompt = cf['prompt'][dg][0]

    if debug:
        print("cli:", cli)
        print("timeout:", timeout)
        print("prompt:", prompt)

    # CLI tuples: (command_line, substitutions, timeout, new_prompt)
    #
    for i, c_ in enumerate(cli):
        if verbose:
            log(f"[{step}.{i:02d}] c = {c_}")

        c = (c_,) if isinstance(c_, str) else c_  # convert it back to a tuple in case of a string

        command = c[0]

        c_len = len(c)
        if c_len > 1:
            if c[1] is not None:
                subs = [params[key] for key in c[1]]
                command = command % tuple(subs)
            if c_len > 2:
                timeout = c[2]
                if c_len > 3:
                    prompt = c[3]

        if verbose:
            print(f"-- {func}: command = {command}, prompt = {prompt}")

        if timeout > 0:
            interact.expect([prompt], timeout=timeout)
        interact.send(command)
        output.append(interact.current_output_clean)

    return output


def lab_save():
    global step

    t = datetime.now().strftime('%Y%m%d%H%M')
    ddhhmm = t[6:12]

    func = "lab_save"

    step += 1
    output = []

    for dg in cf['dgs']:
        if cf[dg] is None:
            continue
        print(f"dg: {dg}")

        with open(cf[dg]['host_file'], 'r') as f:
            hosts = f.read().splitlines()

        if dg in ('pa',):
            ext = "xml"
        elif dg in ('arista', 'cisco', 'nexus',):
            ext = "cfg"
        else:
            ext = "txt"

        for host in hosts:
            if host.startswith('#'):
                print(f"-- host = {host} skipped")
                continue
            print(f"-- host = {host}")

            client = None

            # SSH to login
            #
            try:
                username = cf[dg]['username']
                password = cf[dg]['password']
                if verbose:
                    print(f"-- connect to {host} as {username}..")
                client = paramiko.SSHClient()
                client.load_system_host_keys()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname=host, username=username, password=password, timeout=cf['conn_timeout'])
            except Exception as e:
                print(f"** {func}: dg = {dg}: host = {host}:", e)
                client.close()
                continue  # this hack will enforce continuation to the next host

            try:
                with SSHClientInteraction(client, timeout=10, display=(verbose or debug)) as interact:
                    time_delay = cf[dg]['time_delay']
                    print(f"-- sleep for {time_delay} seconds..")
                    time.sleep(max(1, time_delay))  # wait for at least 3 seconds
                    # interact.send("")
                    output += send_cli(interact,
                                       params={
                                           'dg': dg,
                                           'host': host,
                                           'tftp_host': cf[dg]['tftp_host'],
                                           'file': f"{dg}-{host}-{ddhhmm}.{ext}",
                                       })
            except Exception as e:
                print(f"** {func}: dg = {dg}: host = {host}:", e)
            finally:
                client.close()

    return output


def write_files(data, stats=None):
    global step

    step += 1

    if verbose:
        print(f"-- generate output at {cf['job_dir']}/..")

    file = cf['cnf_file']  # .format(ddhhmm)
    with open(file, 'a') as f:
        cred = [(cf['username'], cf['password'])]
        cf['username'], cf['password'] = '', ''
        for dg in cf['dgs']:
            cred.append((cf[dg]['username'], cf[dg]['password']))
            cf[dg]['username'], cf[dg]['password'] = '', ''
            # del(cf[dg]['username'])
            # del(cf[dg]['password'])

        f.write(json.dumps({'cf': cf, 'metrics': metrics}, indent=4))
        # json.dump({'cf': cf, 'metrics': metrics}, f)

        cf['username'], cf['password'] = cred[0]
        for i, dg in enumerate(cf['dgs'], start=1):
            cf[dg]['username'], cf[dg]['password'] = cred[i]
        if verbose:
            log("[{0:02.2f}] file = {1}".format(step, file))

    file = cf['cli_file']  # .format(ddhhmm)
    with open(file, 'a') as f:
        f.write("\n".join(data))
        if verbose:
            log("[{0:02.2f}] file = {1}".format(step, file))

    if stats is not None:
        file = cf['sta_file']  # .format(ddhhmm)
        with open(file, 'a') as f:
            f.write(json.dumps(stats, indent=4))
            if verbose:
                log("[{0:02.2f}] file = {1}".format(step, file))


def analyze(data):
    global step

    step += 1

    if verbose:
        print(f"-- analyze data..")

    output = {}   # stats
    results = {}  # results extracted from data

    for key in metrics.keys():
        pattern = metrics[key] if isinstance(metrics[key], str) else metrics[key][0]
        results[key] = []
        for i, text in enumerate(data):
            matches = re.findall(pattern, text)
            if matches:
                for m in matches:
                    results[key].append(m)
                    break  # skip the rest of the matches
                if debug:
                    print("matches:", matches)
            if debug:
                print(f"{i} - text =", text)
                print("-" * 80)
        if len(results[key]) == 0:  # delete empty matches from the results
            del results[key]

    for i, key in enumerate(results.keys()):
        values = results[key]
        data_type = 'float' if isinstance(metrics[key], str) else metrics[key][1]
        s = None
        #
        # check data_type of the metric
        #
        if data_type in ('float',):
            v0 = float(values[0])
            s = {
                'min': v0, 'max': v0,
                'ave': 0,
                'cnt': len(values)
            }
            for value in values:
                v = float(value)
                s['min'] = min(s['min'], v)
                s['max'] = max(s['max'], v)
                s['ave'] += v
            s['ave'] /= s['cnt']
        elif data_type in ('str',):
            s = {k: v for k, v in enumerate(values)}  # nothing to calculate
        if verbose:
            j = i * 2
            log("[{0}.{1:02d}] metrics = {2}: {3}".format(step, j, key, values))
            log("[{0}.{1:02d}] stats   = stats: [{2}]".format(step, j + 1, s))
        output[key] = s

    return output


def read_conf(cf_path):
    if not exists(cf_path):
        print("{0}: file not found".format(cf_path))
        exit(1)
    name = "conf"
    spec = importlib.util.spec_from_file_location(name, cf_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='lab-save.py', description='Script to save lab device config.')
    parser.add_argument('-c', '--conf', nargs='?', type=str, default="conf/lab.py", help="config file")
    parser.add_argument('-v', '--verbose', action='store_true', help="verbose mode")
    parser.print_help()
    print()

    args = parser.parse_args()

    if not debug:
        print(args, "\n")

    read_conf(args.conf)
    from conf import cf, metrics

    init()
    data_ = lab_save()
    stats_ = analyze(data_)
    write_files(data_, stats_)

    step += 1

    if verbose:
        log("[{0:02.2f}] job_dir = {1}".format(step, cf['job_dir']), flush=True)
