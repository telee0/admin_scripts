#!/usr/bin/env python3

import argparse
import glob
import ipaddress
import json
import re
import sys
import time
from email.header import decode_header, make_header
from pathlib import Path

import geoip2.database
import pandas as pd

from data.conf import cf
from data.spam import patterns


ctx = {}

def init():
    ctx['start_time'] = time.time()

    ctx['verbose'] = cf['verbose'] or ctx['args'].verbose
    ctx['debug'] = cf['debug']

    log_files = sorted(
        set(Path(file) for pattern in cf['input_patterns'] for file in glob.glob(pattern)),
        key=lambda p: p.stat().st_mtime,
        reverse=False,
    )
    if not log_files:
        print("Error: No log files matched.", file=sys.stderr)
        sys.exit(1)

    n = len(log_files)
    if ctx['args'].input is not None:
        k = ctx['args'].input
        n = min(k, n)

    if ctx['verbose']:
        print(f"init: {n} log_files:", log_files)

    ctx['cache_dir'] = Path(cf['cache_dir'])
    ctx['cache'] = {}
    ctx['data_dir'] = Path(cf['data_dir'])
    ctx['csv_file'] = str(ctx['data_dir'] / cf['csv_file'])
    ctx['ctx_file'] = str(ctx['data_dir'] / cf['ctx_file'])

    if ctx['args'].all:
        patterns['spam']['any'] = (r".*", 0)  # 'any' is the least specific so score 0
    else:
        patterns['spam'].pop('any', None)

    print(ctx['args'], "\n")

    ctx['pattern_spam'] = {}
    ctx['label_score'] = {}
    for label, pattern in patterns['spam'].items():
        if isinstance(pattern, tuple):
            ctx['pattern_spam'][label] = pattern[0]
            ctx['label_score'][label] = pattern[1]
        else:
            ctx['pattern_spam'][label] = pattern
            ctx['label_score'][label] = cf['label_score_default']

    if ctx['debug']:
        print("init: ctx['label_score'] ==", ctx['label_score'])

    reader = geoip2.database.Reader(cf['geoip_db'])

    ctx['no_cache'] = cf['no_cache'] or ctx['args'].no_cache
    ctx['log_files'] = log_files[-n:]
    ctx['reader'] = reader

    ctx['count_by'] = {}
    ctx['count_by']['file'] = {file.name: 0 for file in ctx['log_files']}  # dict instead of list for future use cases
    ctx['count_by']['label'] = {k: 0 for k in ctx['pattern_spam'].keys()}
    ctx['count_by']['labels'] = ctx['count_by']['label']

    try:
        with open(cf['edl_spam'], "r", encoding="utf-8") as f:
            spam_list = f.read().splitlines()  # no trailing newlines
    except FileNotFoundError:
        spam_list = []

    ctx['spam_set'] = set(spam_list)

    ctx['prefix'] = {}
    ctx['prefix_label'] = {}

    ctx['lists'] = ['bl', 'wl']
    ctx['list_columns'] = ['labels']  # columns with a list of values

    for l in ctx['lists']:
        ctx[f'prefix_{l}_file'] = str(ctx['data_dir'] / cf[f'prefix_{l}_file'])
        ctx[f'prefix_{l}'] = []
        try:
            with open(ctx[f'prefix_{l}_file'], "r", encoding="ascii") as f:
                for line in f:
                    line = line.split("#", 1)[0].strip()
                    if line:
                        ctx[f'prefix_{l}'].append(line)
        except Exception as e:
            print('init:', str(e), file=sys.stderr)
            sys.exit(1)
        ctx[f'prefix_{l}_set'] = set(ctx[f'prefix_{l}'])

    if ctx['debug']:
        print(json.dumps(ctx['prefix_wl'], indent=4, skipkeys=True))

    ctx['prefix_cnt'] = {}
    ctx['prefix_label_cnt'] = {}


def cleanup():
    ctx['reader'].close()  # Good practice
    ctx['reader'] = None

    if ctx['spam_set'] != ctx['prefix_bl_set']:  # edl file is stale
        print(f"\ncleanup: writing edl_spam {cf['edl_spam']}")
        prefix_bl_sorted = sorted(ctx['prefix_bl'], key=prefix_order)
        with open(cf['edl_spam'], "w", encoding="ascii", errors="strict") as f:
            for prefix in prefix_bl_sorted:
                f.write(f"{prefix}\n")

    print()
    for cache_file, cache in ctx['cache'].items():
        print(f"go: writing cached data to '{cache_file}'")
        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)

    if ctx['debug']:
        print()
        for key, val in ctx.items():
            print(f"key {key}: {type(val)}")

    ctx['args'] = vars(ctx['args'])
    ctx['log_files'] = [str(file) for file in ctx['log_files']]
    ctx_file = ctx['ctx_file']
    for key, val in ctx.items():
        if isinstance(val, dict):
            for k, v in val.items():
                if isinstance(v, set):
                    val[k] = list(v)
        elif isinstance(val, set):
            ctx[key] = list(val)
        elif isinstance(val, Path):
            ctx[key] = str(val)
    with open(ctx_file, "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2,
            skipkeys=True,
            default=lambda o: '<not serializable>',
        )

    ctx['stop_time'] = time.time()


def get_country(ip_address):
    ip = ipaddress.ip_address(ip_address)
    if ip.is_private:
        return None
    try:
        response = ctx['reader'].country(ip_address)
        return {
            'code': response.country.iso_code,  # e.g., 'US'
            'name': response.country.name       # e.g., 'United States'
        }
    except geoip2.errors.AddressNotFoundError:
        print(f"get_country: {ip_address}: IP not found in database")
    except Exception as e:
        print(f"get_country: {ip_address}: {str(e)}")
    return None


def label_score(x):
    return -ctx['label_score'].get(x, cf['label_score_default']), x


def prefix_order(prefix: str):
    net = ipaddress.ip_network(prefix, strict=False)
    return (
        net.version,
        net.network_address,
        net.prefixlen < 32,  # != 32,  # /32 first
        net.prefixlen
    )


def go():
    patterns_spam = {label: re.compile(pattern, re.IGNORECASE) for label, pattern in ctx['pattern_spam'].items()}

    results = {}

    for log_file in ctx['log_files']:
        cache = {}
        cache_valid = False
        cache_file = (ctx['cache_dir'] / log_file.name).with_suffix('.json')
        if cache_file.exists():
            log_mtime = log_file.stat().st_mtime
            cache_mtime = cache_file.stat().st_mtime
            if cache_mtime >= log_mtime:
                cache_valid = True
        if not ctx['no_cache'] and cache_valid:
            if ctx['verbose']:
                print(f"go: reading cached data from '{cache_file}'")
            with cache_file.open("r", encoding="utf-8") as f:
                cache = json.load(f)
            # results.update(cache)  # not safe as logs of a mail transaction may split during log rotation
            for k, v in cache.items():
                if k in results:
                    results[k].update(v)  # safe merge of mail transaction details
                else:
                    results[k] = v
            continue
        try:
            with log_file.open('r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue

                    key = None
                    for line_type in ('from', 'from_hdr', 'subj_hdr', 'to', 'user'):
                        m = patterns[line_type].search(line)
                        if m:
                            key = m.group('qid')
                            val_dict = m.groupdict()
                            if key in results:
                                results[key].update(val_dict)
                            else:
                                results[key] = val_dict
                                cache[key] = results[key]
                            break
                    if key is None:  # no match
                        continue

                    if 'where' not in results[key]:
                        results[key]['where'] = []
                    results[key]['where'].append((log_file.name, line_num))  # , line))
                    if 'labels' not in results[key]:
                        results[key]['labels'] = []

                    text, text_hdr = None, None

                    if 'from' in val_dict:
                        ip = val_dict['ip']
                        prefix = '.'.join(ip.split('.')[:-1] + ['0/24'])
                        results[key].update(  # remember where this line is
                            {
                                'file': log_file.name,
                                'line': line_num,
                                'prefix': prefix,
                            }
                        )
                        country = get_country(ip)
                        if country is not None:
                            results[key]['country'] = f"{country['name']} ({country['code']})"
                        text = val_dict['from']
                    elif 'from_hdr' in val_dict:
                        text_hdr = 'from_hdr'
                    elif 'subj_hdr' in val_dict:
                        text_hdr = 'subj_hdr'
                    elif 'to' in val_dict:
                        text = val_dict['to']
                    elif 'user' in val_dict:
                        if 'users' not in results[key]:
                            results[key]['users'] = []
                        results[key]['users'].append(val_dict['user'])
                        results[key]['labels'].append('_uu')  # label for email harvesting

                    if text_hdr is not None:
                        text_org = val_dict[text_hdr]
                        results[key][text_hdr + '_org'] = text_org
                        text = str(make_header(decode_header(text_org)))
                        mark = '> ' if text != text_org else ''
                        results[key][text_hdr] = mark + text

                    if text is not None:
                        if 'labels' not in results[key]:
                            results[key]['labels'] = []
                        for label, regex in patterns_spam.items():
                            if regex.search(text):
                                results[key]['labels'].append(label)  # all labels
        except Exception as e:
            print(f"go: error reading {log_file}: {e}", file=sys.stderr)

        ctx['cache'][cache_file] = cache

    incomplete = []
    for key, val_dict in results.items():
        if 'labels' in val_dict:
            labels = list(set(val_dict['labels']))
        else:
            labels = []
        val_dict['labels'] = labels
        if 'prefix' not in val_dict:
            incomplete.append(key)
            continue
        prefix = val_dict['prefix']
        ip = val_dict['ip']
        for l in ctx['lists']:
            if prefix in ctx[f"prefix_{l}_set"] or ip in ctx[f"prefix_{l}_set"]:
                val_dict[f'in_{l}'] = True

    ctx['incomplete'] = {}
    for key in incomplete:
        ctx['incomplete'][key] = results[key]
        del results[key]
        if ctx['verbose']:
            print(f"go: results['{key}'] removed")

    if ctx['args'].unlisted_only:
        results_filtered = {}
        for key, val_dict in results.items():
            if any(f"in_{l}" in val_dict for l in ctx['lists']):
                continue
            results_filtered[key] = val_dict
        results = results_filtered

    for val_dict in results.values():
        prefix = val_dict['prefix']
        ip = val_dict['ip']
        labels = sorted(list(set(val_dict['labels'])), key=label_score)
        val_dict['labels'] = labels
        val_dict['label'] = labels[0] if len(labels) > 0 else None
        if prefix not in ctx['prefix']:
            ctx['prefix'][prefix] = set()
        ctx['prefix'][prefix].add(ip)
        if prefix not in ctx['prefix_label']:
            ctx['prefix_label'][prefix] = set()
        ctx['prefix_label'][prefix].update(set(labels))

    if ctx['debug']:
        print(json.dumps(results, indent=4))

    return results


def tab_list(data_dict, sort_by=cf['sort_by']):
    if not data_dict:
        print("No matches found.")
        sys.exit(0)

    # for each prefix, count its labels, and IP explicitly in the BL/WL
    #
    prefix_set = set()
    for prefix, ip_set in ctx['prefix'].items():
        prefix_set.add(prefix)
        prefix_set.update(ip_set)
        cnt, cnt_str = {}, {}
        for l in ctx['lists']:
            if prefix in ctx[f"prefix_{l}"]:
                cnt[l] = 256
            else:
                cnt[l] = len(ip_set & ctx[f"prefix_{l}_set"])
            cnt_str[l] = "" if cnt[l] == 0 else "Yes" if cnt[l] == 256 else str(cnt[l])
        ctx['prefix_cnt'][prefix] = f"{cnt_str['bl']:>3} {cnt_str['wl']:>3}"
        ctx['prefix_label_cnt'][prefix] = len(ctx['prefix_label'][prefix])

        labels = ctx['prefix_label'][prefix]
        ctx['prefix_label'][prefix] = sorted(list(labels), key=label_score)

    filtered = {k: v for k, v in data_dict.items() if 'label' in v and 'country' in v}

    df = pd.DataFrame.from_dict(filtered, orient='index')
    df = df.reindex(columns=cf['col_all']).fillna('')
    df = df.sort_values(by=sort_by, ascending=True)

    df.to_csv(ctx['csv_file'].format(''), index=False)

    for column, width in cf['col_widths'].items():
        if column in df.columns:
            df[column] = df[column].str[:width]

    if ctx['verbose']:
        print()
        print(df[cf['col_view']].to_string(header=True, index=False))
        print("\nRow count:", len(df))

    for column in cf['count_by']:
        if column in ctx['list_columns']:
            df_column = df[[column]].explode(column).reset_index(drop=True)
        else:
            df_column = df

        if isinstance(column, tuple):
            column, top_n = column
        else:
            top_n = cf['top_n']

        if column in ctx['count_by']:
            values_all = ctx['count_by'][column].keys()
        else:
            values_all = df[column].unique().tolist()

        df_count = (df_column[column]
                    .astype(str)
                    .value_counts()
                    .reindex(values_all, fill_value=0)
                    .reset_index()
                    # .rename(columns={'index': column, column: 'count'})  # restored in prod environment
                    .sort_values(['count', column], ascending=[False, True])
                    .reset_index(drop=True)
                    .head(top_n)
                    )

        if column in ctx:
            df_count[' bl  wl'] = df_count[column].map(lambda k: ctx[column + '_cnt'][k] if k in ctx[column + '_cnt'] else "")
            df_count['cnt'] = df_count[column].map(lambda k: len(ctx[column][k]) if k in ctx[column] else 0)

        col_label = f"{column}_label"
        if col_label in ctx:
            df_count['cnt_l'] =df_count[column].map(
                lambda k: f"{ctx[col_label + '_cnt'][k]}" if k in ctx[col_label] else "")
            df_count['labels'] =df_count[column].map(
                lambda k: ' '.join(ctx[col_label][k]) if k in ctx[col_label] else "")

        df_count.to_csv(ctx['csv_file'].format('_count_' + column), index=False)

        print()
        print(df_count.to_string(header=True, index=True))
        print("\nRow sum:", df_count['count'].sum())

    if not ctx['args'].unlisted_only:
        for l in ctx['lists']:
            prefix_set_unseen = ctx[f"prefix_{l}_set"] - prefix_set
            prefix_unseen_sorted = sorted(prefix_set_unseen, key=prefix_order)
            print(f"\nPrefixes unseen from list {l}:", json.dumps(prefix_unseen_sorted, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='spam-check.py',
        description='Script to identify spamming from maillog',
        add_help=True
    )
    parser.add_argument('-a', '--all', action='store_true', help="include all entries")
    parser.add_argument(
        '-n',
        '--input', type=int, metavar="K",
        default=None,
        help="process only the K most recent log files"
    )
    parser.add_argument('--no-cache', action='store_true', help="ignore cached JSON files")
    parser.add_argument(
        "--unlisted-only",  # command-line flag
        action="store_true",
        help="show only entries where IP and prefix are in neither the blacklist nor the whitelist"
    )
    parser.add_argument('-v', '--verbose', action='store_true', help="verbose")
    parser.print_help()
    print()

    ctx['args'] = parser.parse_args()

    init()
    mail_records = go()
    tab_list(mail_records)
    cleanup()

    print(f"\nTime of execution: {ctx['stop_time'] - ctx['start_time']:.3f}s")
    print(f"Time of execution: {ctx['stop_time'] - ctx['start_time']:.3f}s\n", file=sys.stderr)
