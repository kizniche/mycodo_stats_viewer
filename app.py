# -*- coding: utf-8 -*-
import argparse
import calendar
import logging
import time
import timeit
from collections import OrderedDict
from datetime import datetime

import os
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
from flask_influxdb import InfluxDB

from config import COLUMNS
from config import PI_VERSIONS
from config import STATS
from secret_variables import INFLUXDB_DATABASE
from secret_variables import OWN_IDS

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, template_folder=tmpl_dir)
influx_db = InfluxDB(app)

app.config['INFLUXDB_DATABASE'] = INFLUXDB_DATABASE


@app.route('/', methods=('GET', 'POST'))
def default_page():
    timer = timeit.default_timer()
    timeframe = '3'
    sort_type = 'Mycodo_revision'
    if request.method == 'POST':
        sort_type = request.form['sorttype']
        timeframe = request.form['timeframe']

    stats_data = get_stats_data(timeframe)
    parsed_data = {}

    def get_value(data_input, data_name, return_type):
        if data_input['name'] == data_name:
            for key, value in data_input.items():
                if key == 'values':
                    if return_type == 'int':
                        parsed_data[each_id][data_name] = '{}'.format(int(float(value[0][1])))
                    elif return_type == 'float':
                        parsed_data[each_id][data_name] = '{:.1f}'.format(float(value[0][1]))
                    elif return_type == 'str':
                        parsed_data[each_id][data_name] = '{}'.format(str(value[0][1]))

    ids, number_installed_devices = get_ids(sort_type, timeframe)
    for each_id, _ in ids.items():
        parsed_data[each_id] = {}
        for known_id, own_host in OWN_IDS.items():
            if known_id == each_id:
                parsed_data[each_id]['host'] = own_host
                break
        if 'host' not in parsed_data[each_id]:
            parsed_data[each_id]['host'] = each_id

        for series in stats_data['series']:
            if series['tags']['anonymous_id'] == each_id:
                if series['name'] == 'Mycodo_revision':
                    for key, value in series.items():
                        if key == 'values':
                            # Convert UTC timestamp to local server timezone
                            utc_datetime = datetime.strptime(value[0][0][0:19], "%Y-%m-%dT%H:%M:%S")
                            now_timestamp = time.time()
                            offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
                            parsed_data[each_id]['time'] = datetime.strftime(utc_datetime + offset, "%Y-%m-%d %H:%M:%S")
                            break

                for stat, stat_type, _ in STATS:
                    get_value(series, stat, stat_type)

        if parsed_data[each_id]['RPi_revision'] in PI_VERSIONS:
            parsed_data[each_id]['RPi_revision'] = PI_VERSIONS[parsed_data[each_id]['RPi_revision']]

        if 'alembic_version' in parsed_data[each_id]:
            parsed_data[each_id]['alembic_version'] = parsed_data[each_id]['alembic_version'][:4]

        if 'time' in parsed_data[each_id]:
            parsed_data[each_id]['time'] = parsed_data[each_id]['time'][:-3]

    countries_count = {}
    for each_id, _ in parsed_data.items():
        if 'country' in parsed_data[each_id]:
            if parsed_data[each_id]['country'] in countries_count:
                countries_count[parsed_data[each_id]['country']] += 1
            else:
                countries_count[parsed_data[each_id]['country']] = 1

    # Get data for chart
    past_stats_count = past_stats_data_count()

    app.logger.info("{name}: Completion time: {time} seconds".format(
      name=__name__, time=timeit.default_timer() - timer))

    return render_template('index.html',
                           columns=COLUMNS,
                           timeframe=timeframe,
                           sort_type=sort_type,
                           stats_data=stats_data,
                           ids=ids,
                           countries_count=countries_count,
                           number_installed_devices=number_installed_devices,
                           own_ids=OWN_IDS,
                           parsed_data=parsed_data,
                           past_stats_count=past_stats_count,
                           pi_versions=PI_VERSIONS,
                           stats=STATS)


@app.route('/id/<stat_id>', methods=('GET', 'POST'))
def id_stats(stat_id):
    timer = timeit.default_timer()
    stats_data_id = get_stats_data_id(stat_id)
    parsed_data = {}

    def get_values(data_input, data_name, return_type):
        if data_input['name'] == data_name:
            parsed_data[data_name] = []
            for key, value in data_input.items():
                if key == 'values':
                    if return_type == 'int':
                        for each_value in value:
                            parsed_data[data_name].append('{}'.format(int(float(each_value[1]))))
                    elif return_type == 'float':
                        for each_value in value:
                            parsed_data[data_name].append('{:.1f}'.format(float(each_value[1])))
                    elif return_type == 'str':
                        for each_value in value:
                            parsed_data[data_name].append('{}'.format(str(each_value[1])))

    for series in stats_data_id['series']:
        if series['name'] == 'RPi_revision':
            parsed_data['time'] = []
            for key, value in series.items():
                if key == 'values':
                    for each_value in value:
                        time_obj = time.strptime(each_value[0][0:19], "%Y-%m-%dT%H:%M:%S")
                        parsed_data['time'].append(time.strftime("%Y-%m-%d %H:%M:%S", time_obj))

        for stat, stat_type, _ in STATS:
            get_values(series, stat, stat_type)

    app.logger.info("{name}: Completion time: {time} seconds".format(
      name=__name__, time=timeit.default_timer() - timer))

    return render_template('details.html',
                           stats_data_id=stats_data_id,
                           own_ids=OWN_IDS,
                           parsed_data=parsed_data,
                           pi_versions=PI_VERSIONS,
                           stats=STATS)


def format_datetime(value):
    utc_dt = datetime.strptime(value.split(".")[0], '%Y-%m-%dT%H:%M:%S')
    utc_timestamp = calendar.timegm(utc_dt.timetuple())
    return str(datetime.fromtimestamp(utc_timestamp).strftime('%Y/%m/%d %H:%M'))

app.jinja_env.filters['datetime'] = format_datetime


def past_stats_data_count():
    """Return data from past_seconds until present from influxdb"""
    dbcon = influx_db.connection
    try:
        query_str = """SELECT DISTINCT("anonymous_id")
                       FROM (SELECT value, "anonymous_id" FROM num_relays)
                       GROUP BY time(7d)
                    """

        raw_data = dbcon.query(query_str).raw

        dict_day_number_users = {}
        for each_set in raw_data['series'][0]['values']:
            if each_set[0] not in dict_day_number_users:
                dict_day_number_users[each_set[0]] = 0
            dict_day_number_users[each_set[0]] += 1

        return dict_day_number_users

    except Exception as e:
        return None


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
    """Return all statistics data for the past time_days days"""
    dbcon = influx_db.connection
    raw_data = dbcon.query("""SELECT last(value)
                              FROM /.*/
                              WHERE time > now() - {time}d
                              GROUP BY *
                              ORDER BY time DESC
                              LIMIT 1
                           """.format(time=time_days)).raw
    return raw_data


def get_ids(measurement, time_days):
    """Return a dictionary of user ids sorted based on measurement"""
    number_installed_devices = 0
    dbcon = influx_db.connection
    raw_data = dbcon.query("""SELECT value
                              FROM {measurement}
                              WHERE time > now() - {time}d
                              GROUP BY *
                              ORDER BY time DESC
                              LIMIT 1
                           """.format(measurement=measurement,
                                      time=time_days)
                           ).raw

    # Create dictionary of ID (value) and category (value)
    dict_ids = {}
    for key, value in raw_data.items():
        if value != 0:
            for each_value in value:
                dict_ids[each_value['tags']['anonymous_id']] = each_value['values'][0][1]
                if len(each_value['tags']['anonymous_id']) == 10:
                    number_installed_devices += 1

    # Sort lowest to highest by values (measurement)
    sorted_dict_ids = OrderedDict()
    s = [(k, dict_ids[k]) for k in sorted(dict_ids, key=dict_ids.get, reverse=False)]
    for key, value in s:
        sorted_dict_ids[key] = value

    # for key, value in sorted(dict_ids.iteritems(), key=lambda (k, v): (v, k)):
    #     sorted_dict_ids[key] = value

    # Reverse sorting (highest to lowest values)
    resorted_dict_ids = OrderedDict(reversed(list(sorted_dict_ids.items())))

    return resorted_dict_ids, number_installed_devices


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Mycodo Viewer Flask HTTP server",
        formatter_class=argparse.RawTextHelpFormatter)

    options = parser.add_argument_group('Options')
    options.add_argument('-d', '--debug', action='store_true',
                         help="Run Flask with debug=True (Default: False)")

    args = parser.parse_args()
    debug = args.debug

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)

    app.run(host='0.0.0.0', port=5000, debug=debug)
