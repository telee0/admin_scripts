import re

patterns = {
    'from': re.compile(
        r'''
        sendmail\[(?P<pid>\d+)]:\s*
        (?P<qid>[^:]+):\s*
        from=<(?P<from>[^>]*)>,
        .*?
        \[(?P<ip>(?:\d{1,3}\.){3}\d{1,3})]
        ''',
        re.VERBOSE | re.IGNORECASE
    ),
    'from_hdr': re.compile(
        r'''
        sendmail\[(?P<pid>\d+)]:\s*
        (?P<qid>[^:]+):\s*
        From:\s*(?P<from_hdr>.+)
        ''', re.VERBOSE | re.IGNORECASE
    ),
    'subj_hdr': re.compile(
        r'''
        sendmail\[(?P<pid>\d+)]:\s*
        (?P<qid>[^:]+):\s*
        Subject:\s*(?P<subj_hdr>.+)
        ''', re.VERBOSE | re.IGNORECASE
    ),
    'to': re.compile(
        r'''
        sendmail\[(?P<pid>\d+)]:\s*
        (?P<qid>[^:]+):\s*
        to=<(?P<to>[^>]+)>,
        ''', re.VERBOSE | re.IGNORECASE
    ),
    'user': re.compile(
        r'''
        sendmail\[(?P<pid>\d+)]:\s*
        (?P<qid>[^:]+):\s*
        <(?P<user>[^>]+)>\.\.\.\s+User\sunknown
        ''', re.VERBOSE | re.IGNORECASE
    ),
    'spam': {
        "$": (r"\$[0-9]+", 2),
        "aaa": r"aaa",
        "aarp": (r"aarp", 2),
        "ace": r"ace",
        "adt": (r"adt", 2),
        "ahs": (r"ahs", 2),
        "ain": r"ain",
        # "apple": r"apple",
        "aura": r"aura",
        "auto": r"auto",
        "b.ue": r"b.ue",
        "bcbs": (r"bcbs", 2),
        "butc": r"butc",
        "cash": r"cash",
        # "coin": r"coin",
        "costco": (r"c[o0]stc[o0]", 2),
        "dhu": r"dhu",
        "docusign": r"docusign",
        "earn": r"earn",
        "fed": r"fed",
        "finan": r"finan",
        "gov": r"gov",
        "harr": r"harr",
        "home": r"home",
        "income": r"income",
        "iptv": r"iptv",
        "itx": r"itx",
        "kcp": r"kcp",
        "lowes": (r"lowes", 2),
        "lux": r"lux",
        "marr": (r"marr", 2),
        "money": r"money",
        "omaha": (r"[o0]maha", 2),
        "order": r"order",
        "pay": r"pay",
        "phantom": r"phantom",
        # "photog": r"photog",
        "press": r"press",
        "reg": r"reg",
        "samp": r"samp",
        "sba": r"sba",
        "schk": r"schk",
        # "secret": r"secret",
        "solana": r"solana",
        # "ssa": r"ssa",
        "steak": r"steak",
        "supp": r"supp",
        "tax": r"tax",
        "temu": r"temu",
        "ticket": r"ticket",
        "toll": r"to([il1])\1",
        "triple": r"triple",
        "uob": r"uob",
        "vault": r"vault",
        "vit": r"vit",
        "vui": r"vui",
        "w8ben": r"w.?8ben",

        # "amy": r"amy",
        # "app": r"app",
        # "auone": r"auone",
        # "bit": r"bit",
        # "dhabi": r"dhabi",
        # "team": r"team",
    },
}


if __name__ == "__main__":
    pass