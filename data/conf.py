
cf = {
    'ver': '1.7 [20260305]',
    'input_patterns': ["data/maillog/*"],
    'geoip_db': 'data/GeoLite2-Country.mmdb',
    # 'input_patterns': ["/var/log/maillog*"],
    # 'geoip_db': '/home/terence/bin/GeoLite2-Country.mmdb',
    'edl_spam': 'data/spam.txt',
    'no_cache': False,
    'cache_dir': 'data',
    'data_dir': 'data',
    'prefix_wl_file': 'prefix_wl.txt',
    'prefix_bl_file': 'prefix_bl.txt',
    'csv_file': 'df{}.csv',
    'ctx_file': 'ctx.json',
    #
    'col_all':  ['file', 'line', 'ip', 'prefix', 'country', 'from', 'to', 'from_hdr', 'subj_hdr', 'label', 'labels', 'in_bl', 'in_wl'],  # 'pid', 'qid'],
    'col_view': ['file', 'line', 'ip',           'country', 'from',       'from_hdr', 'subj_hdr', 'label'],
    'col_widths': {'from': 40, 'from_hdr': 60, 'subj_hdr': 80},
    'sort_by': ['ip', 'label'],
    'count_by': ['labels', 'country', 'file', ('prefix', 1000), 'to'],
    'top_n': 100,
    'label_score_default': 1,
    'verbose': False,
    'debug': False,
}


if __name__ == "__main__":
    pass