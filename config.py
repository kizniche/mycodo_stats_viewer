# -*- coding: utf-8 -*-

STATS = [
    ('uptime', 'float', 'Uptime'),
    ('os_version', 'str', 'OS'),
    ('Mycodo_revision', 'str', 'Mycodo Version'),
    ('alembic_version', 'str', 'Alembic Version'),
    ('RPi_revision', 'str', 'RPi Version'),
    ('country', 'str', 'Country'),
    ('daemon_startup_seconds', 'float', 'Startup Seconds'),
    ('ram_use_mb', 'float', 'Ram Use'),
    ('num_relays', 'int', 'Number of Outputs'),
    ('num_sensors_active', 'int', 'Inputs Active'),
    ('num_sensors', 'int', 'Inputs'),
    ('num_maths_active', 'int', 'Maths Active'),
    ('num_maths', 'int', 'Maths'),
    ('num_conditionals_active', 'int', 'Conditionals Active'),
    ('num_conditionals', 'int', 'Conditionals'),
    ('num_triggers_active', 'int', 'Triggers Active'),
    ('num_triggers', 'int', 'Triggers'),
    ('num_methods_in_pid', 'int', 'Methods in PIDs'),
    ('num_methods', 'int', 'Mthods'),
    ('num_pids_active', 'int', 'PIDs Active'),
    ('num_pids', 'int', 'PIDs'),
    ('num_lcds_active', 'int', 'LCDs Active'),
    ('num_lcds', 'int', 'LCDs')
]

COLUMNS = [
    ('ID', 'id', ''),
    ('Last', 'last', ''),
    ('Up', 'uptime', ''),
    ('OS', 'os_version', ''),
    ('M.v', 'Mycodo_revision', ''),
    ('A.v', 'alembic_version', ''),
    ('Pi', 'RPi_revision', ''),
    ('Loc', 'country', ''),
    ('Strt', 'daemon_startup_seconds', ''),
    ('RAM', 'ram_use_mb', ''),
    ('Out', 'num_relays', ''),
    ('In', 'num_sensors', 'num_sensors_active'),
    ('Ma', 'num_maths', 'num_maths_active'),
    ('Con', 'num_conditionals', 'num_conditionals_active'),
    ('Tr', 'num_triggers', 'num_triggers_active'),
    ('Me', 'num_methods', 'num_methods_in_pid'),
    ('PID', 'num_pids', 'num_pids_active'),
    ('LCD', 'num_lcds', 'num_lcds_active')
]

PI_VERSIONS = {
    'Beta': '1Beta',
    '0002': '1B',
    '0003': '1B',  # ECN0001
    '0004': '1B',
    '0005': '1B',
    '0006': '1B',
    '0007': '1A',
    '0008': '1A',
    '0009': '1A',
    '0010': '1B+',
    '000d': '1B',
    '000e': '1B',
    '000f': '1B',
    '100000e': '1B',
    '0011': 'CM1',
    '0012': '1A+',
    '0013': '1B+',
    '0014': 'CM1',
    '0015': '1A+',
    '2a01041': '2B',
    'a22082': '3B',
    'a020d3': '3B+',

    '900021': '1A+',  # Sony UK
    '900032': '1B+',  # Sony UK
    '900092': 'Zero',  # Sony UK
    '900093': 'Zero',  # Sony UK
    '9000c1': 'ZeroW',  # Sony UK
    '920093': 'Zero',  # Embest
    'a01040': '2B',  # Sony UK
    'a01041': '2B',  # Sony UK
    'a02082': '3B',  # Sony UK
    'a020a0': 'CM3',  # & Lite, Sony UK
    'a52082': '3B',  # Stadium
    'a21041': '2B',  # Embest
    'a22042': '2B',  # BCM2837
    '2a02082': '3B',  # Embest
    'a32082': '3BJap',  # Japan
    '1a22082': '3BUnk',  # Unknown
    
    'a03111': '4B',
    'b03111': '4B',
    'c03111': '4B',
}
