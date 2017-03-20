# -*- coding: utf-8 -*-
import os
from secret_variables import INFLUXDB_USER
from secret_variables import INFLUXDB_PASSWORD
from secret_variables import INFLUXDB_DATABASE
from secret_variables import OWN_IDS

STATS = [
    ('uptime', 'float', 'Uptime'),
    ('Mycodo_revision', 'str', 'Mycodo Version'),
    ('alembic_version', 'str', 'Alembic Version'),
    ('RPi_revision', 'str', 'RPi Version'),
    ('country', 'str', 'Country'),
    ('daemon_startup_seconds', 'float', 'Startup Seconds'),
    ('ram_use_mb', 'float', 'Ram Use'),
    ('num_users_guest', 'int', 'Number of Guests'),
    ('num_users_admin', 'int', 'Number of Admins'),
    ('num_relays', 'int', 'Number of Relays'),
    ('num_sensors_active', 'int', 'Sensors Active'),
    ('num_sensors', 'int', 'Sensors'),
    ('num_conditionals_active', 'int', 'Conditionals Active'),
    ('num_conditionals', 'int', 'Conditoinals'),
    ('num_timers_active', 'int', 'Timers Active'),
    ('num_timers', 'int', 'Timers'),
    ('num_methods_in_pid', 'int', 'Methods in PIDs'),
    ('num_methods', 'int', 'Mthods'),
    ('num_pids_active', 'int', 'PIDs Active'),
    ('num_pids', 'int', 'PIDs'),
    ('num_lcds_active', 'int', 'LCDs Active'),
    ('num_lcds', 'int', 'LCDs'),
    ('next_send', 'int', 'Next Send')
]

COLUMNS = [
    ('ID', 'id', ''),
    ('Last', 'last', ''),
    ('Up', 'uptime', ''),
    ('M Ver.', 'Mycodo_revision', ''),
    ('A Ver.', 'alembic_version', ''),
    ('Pi', 'RPi_revision', ''),
    ('Loc', 'country', ''),
    ('Start', 'daemon_startup_seconds', ''),
    ('RAM', 'ram_use_mb', ''),
    ('Gst', 'num_users_guest', ''),
    ('Adm', 'num_users_admin', ''),
    ('Rel', 'num_relays', ''),
    ('Sens', 'num_sensors', 'num_sensors_active'),
    ('Cond', 'num_conditionals', 'num_conditionals_active'),
    ('Tim', 'num_timers', 'num_timers_active'),
    ('Meth', 'num_methods', 'num_methods_in_pid'),
    ('PID', 'num_pids', 'num_pids_active'),
    ('LCD', 'num_lcds', 'num_lcds_active'),
    ('Next', 'next_send', '')
]

PI_VERSIONS = {
    'Beta':'1 Beta',
    '0002':'1 B',
    '0003':'1 B (ECN0001)',
    '0004':'1 B',
    '0005':'1 B',
    '0006':'1 B',
    '000d':'1 B',
    '100000e':'1 B',
    '000e':'1 B',
    '000f':'1 B',
    '0007':'1 A',
    '0008':'1 A',
    '0009':'1 A',
    '0010':'1 B+',
    '0011':'Compute Mod',
    '0012':'1 A+',
    '0013':'1 B+',
    '0014':'Computer Mod',
    '0015':'1 A+',
    'a21041':'2 B',
    'a01041':'2 B',
    '2a01041':'2 B',
    '900092':'Zero',
    '900093':'Zero',
    '920093':'Zero',
    '9000c1':'ZeroW',
    'a02082':'3 B',
    'a22082':'3 B',
    '2a02082':'3 B'
}
