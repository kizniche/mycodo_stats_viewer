#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import calendar
import operator
import os
from collections import OrderedDict
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_influxdb import InfluxDB
from influxdb import InfluxDBClient

from config import INFLUXDB_USER
from config import INFLUXDB_PASSWORD
from config import INFLUXDB_DATABASE

# Dictionary used to easily distinguish my own devices
from config import OWN_IDS

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, template_folder=tmpl_dir)
influx_db = InfluxDB(app)

app.config['INFLUXDB_USER'] = INFLUXDB_USER
app.config['INFLUXDB_PASSWORD'] = INFLUXDB_PASSWORD
app.config['INFLUXDB_DATABASE'] = INFLUXDB_DATABASE

@app.route('/', methods=('GET', 'POST'))
def default_page():
    timeframe = '3'
    sort_type = 'country'
    if request.method == 'POST':
        sort_type = request.form['sorttype']
        timeframe = request.form['timeframe']
    return render_template('index.html',
                           timeframe=timeframe,
                           sort_type=sort_type,
                           stats_data=get_stats_data(timeframe),
                           ids=get_ids(sort_type, timeframe),
                           own_ids=OWN_IDS,
                           pi_versions=get_pi_versions())


@app.route('/id/<stat_id>', methods=('GET', 'POST'))
def id_stats(stat_id):
    return render_template('details.html',
                           stats_data_id=get_stats_data_id(stat_id),
                           own_ids=OWN_IDS,
                           pi_versions=get_pi_versions())


def format_datetime(value):
    utc_dt = datetime.strptime(value.split(".")[0], '%Y-%m-%dT%H:%M:%S')
    utc_timestamp = calendar.timegm(utc_dt.timetuple())
    return str(datetime.fromtimestamp(utc_timestamp).strftime('%Y/%m/%d %H:%M'))

app.jinja_env.filters['datetime'] = format_datetime


def get_stats_data_id(stat_id):
    """Return all statistics data for an id"""
    dbcon = influx_db.connection
    raw_data = dbcon.query("""SELECT value
                              FROM /.*/
                              WHERE anonymous_id = '{}'
                              GROUP BY *
                              ORDER BY time DESC
                           """.format(stat_id)).raw
    return raw_data


def get_stats_data(time_days):
    """Return all statistics data for the past 5 days"""
    dbcon = influx_db.connection
    raw_data = dbcon.query("""SELECT value
                              FROM /.*/
                              WHERE time > now() - {}d
                              GROUP BY *
                              ORDER BY time DESC
                              LIMIT 1
                           """.format(time_days)).raw
    return raw_data


def get_ids(measurement, time_days):
    """Return a dictionary of user ids sorted based on measurement"""
    dbcon = influx_db.connection
    raw_data = dbcon.query("""SELECT value
                              FROM {}
                              WHERE time > now() - {}d
                              GROUP BY *
                              ORDER BY time DESC
                              LIMIT 1
                           """.format(measurement, time_days)).raw

    # Create dictionary of ID (value) and category (value)
    dict_ids = {}
    for key, value in raw_data.iteritems():
        for each_value in value:
            dict_ids[each_value['tags']['anonymous_id']] = each_value['values'][0][1]

    # Sort lowest to highest by values (measurement)
    sorted_dict_ids = OrderedDict()
    for key, value in sorted(dict_ids.iteritems(), key=lambda (k,v): (v,k)):
        sorted_dict_ids[key] = value

    # Reverse sorting (highest to lowest values)
    resorted_dict_ids = OrderedDict(reversed(list(sorted_dict_ids.items())))

    return resorted_dict_ids


def get_pi_versions():
    """Returns a dictionary of raspberry pi revisions and models"""
    return {
        'Beta':'1 Beta',
        '0002':'1 B',
        '0003':'1 B (ECN0001)',
        '0004':'1 B',
        '0005':'1 B',
        '0006':'1 B',
        '000d':'1 B',
        '0003':'1 B',
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
        '900092':'Zero',
        '900093':'Zero',
        'a02082':'3 B',
        'a22082':'3 B',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Mycodo Flask HTTP server.",
                                     formatter_class=argparse.RawTextHelpFormatter)

    options = parser.add_argument_group('Options')
    options.add_argument('-d', '--debug', action='store_true',
                              help="Run Flask with debug=True (Default: False)")

    args = parser.parse_args()

    if args.debug:
        debug=True
    else:
        debug=False

    app.run(host='0.0.0.0', debug=debug)