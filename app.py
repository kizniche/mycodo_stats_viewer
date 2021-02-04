# -*- coding: utf-8 -*-
import argparse
import calendar
import grp
import logging
import pwd
import socket
import subprocess
import threading
import time
import timeit
import zipfile
from collections import OrderedDict
from datetime import datetime
from influxdb import InfluxDBClient
import io
import natsort
import os
import shutil
from flask import Flask
from flask import render_template
from flask import request
from flask import send_file
from flask_influxdb import InfluxDB

from config import COLUMNS
from config import PI_VERSIONS
from config import STATS
from config import VERSION
from secret_variables import INFLUXDB_DATABASE
from secret_variables import OWN_IDS

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, template_folder=tmpl_dir)
influx_db = InfluxDB(app)

gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

app.config['INFLUXDB_DATABASE'] = INFLUXDB_DATABASE


@app.route('/', methods=('GET', 'POST'))
def default_page():
    timer = timeit.default_timer()
    timeframe = '3'
    sort_type = 'Mycodo_revision'
    if request.method == 'POST':
        sort_type = request.form['sorttype']
        timeframe = request.form['timeframe']

    app.logger.debug("0: {} sec".format(timeit.default_timer() - timer))

    stats_data = get_stats_data(timeframe)
    parsed_data = {}

    app.logger.debug("1: {} sec".format(timeit.default_timer() - timer))

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

    app.logger.debug("2: {} sec".format(timeit.default_timer() - timer))

    ids, number_installed_devices = get_ids(stats_data, sort_type, timeframe)

    app.logger.debug("3: {} sec".format(timeit.default_timer() - timer))

    for each_id in ids:
        parsed_data[each_id] = {}
        if each_id in OWN_IDS:
            parsed_data[each_id]['host'] = OWN_IDS[each_id]
        else:
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

    app.logger.debug("4: {} sec".format(timeit.default_timer() - timer))

    countries_count = {}
    for each_id in parsed_data:
        if 'country' in parsed_data[each_id]:
            if parsed_data[each_id]['country'] in countries_count:
                countries_count[parsed_data[each_id]['country']] += 1
            else:
                countries_count[parsed_data[each_id]['country']] = 1

    app.logger.debug("5: {} sec".format(timeit.default_timer() - timer))

    # Get data for chart
    past_stats_count = past_stats_data_count()

    app.logger.debug("6: {} sec".format(timeit.default_timer() - timer))

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

    # Get version history for chart
    list_versions = []
    last_version = None
    for series in stats_data_id['series']:
        if series["name"] == 'Mycodo_revision':
            for each_value in series["values"]:
                if each_value[1] != last_version:
                    last_version = each_value[1]
                    list_versions.append([each_value[0].replace("T", " "), each_value[1].split(".")])

    list_versions.reverse()

    app.logger.info("{name}: Completion time: {time} seconds".format(
      name=__name__, time=timeit.default_timer() - timer))

    return render_template('details.html',
                           list_versions=list_versions,
                           stats_data_id=stats_data_id,
                           own_ids=OWN_IDS,
                           parsed_data=parsed_data,
                           pi_versions=PI_VERSIONS,
                           stats=STATS)


@app.route('/export', methods=('GET', 'POST'))
def export():
    influx_backup_dir = '/tmp/influx_backup'

    # Delete (if it exists) and create influxdb directory to make sure it's empty
    if os.path.isdir(influx_backup_dir):
        shutil.rmtree(influx_backup_dir)
    assure_path_exists(influx_backup_dir)

    cmd = "/usr/bin/influxd backup -database {db} -portable {path}".format(
        db=INFLUXDB_DATABASE, path=influx_backup_dir)
    _, _, status = cmd_output(cmd)

    influxd_version_out, _, _ = cmd_output('/usr/bin/influxd version')
    if influxd_version_out:
        influxd_version = influxd_version_out.decode('utf-8').split(' ')[1]
    else:
        influxd_version = None
        app.logger.error("Could not determine Influxdb version")

    if not status and influxd_version:
        # Zip all files in the influx_backup directory
        data = io.BytesIO()
        with zipfile.ZipFile(data, mode='w') as z:
            for _, _, files in os.walk(influx_backup_dir):
                for filename in files:
                    z.write(os.path.join(influx_backup_dir, filename), filename)
        data.seek(0)

        # Delete influxdb directory if it exists
        if os.path.isdir(influx_backup_dir):
            shutil.rmtree(influx_backup_dir)

        # Send zip file to user
        return send_file(
            data,
            mimetype='application/zip',
            as_attachment=True,
            attachment_filename='Mycodo_Stats_{dt}_Ver_{mv}_Influxdb_{iv}_{host}.zip'.format(
                mv=VERSION, iv=influxd_version,
                host=socket.gethostname().replace(' ', ''),
                dt=datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        )


@app.route('/import', methods=('GET', 'POST'))
def page_import():
    status = []

    if request.method == 'POST':
        if 'file' not in request.files:
            status.append('No file part')
        elif request.files['file'] == '':
            status.append('No selected file')
        else:
            restore_influxdb = import_influxdb(request)
            if restore_influxdb == 'success':
                status.append(
                    'The influxdb database import has been initialized. '
                    'This process may take an extended time to complete '
                    'if there is a lot of data. Please allow ample time '
                    'for it to complete.')
            else:
                status.append(
                    'Errors occurred during the influxdb database import.')

    return render_template('import.html',
                           status=status)


def thread_import_influxdb(tmp_folder):
    mycodo_db = 'mycodo_stats'
    mycodo_db_backup = 'mycodo_stats_db_bak'
    # dbcon = influx_db.connection
    client = InfluxDBClient(
        'localhost',
        '8086',
        'root',
        'root',
        mycodo_db_backup)

    # Delete any backup database that may exist (can't copy over a current db)
    # dbcon.query('DROP DATABASE "{}"'.format(mycodo_db_backup))
    try:
        client.drop_database(mycodo_db_backup)
    except Exception as msg:
        app.logger.error("Error while deleting db prior to restore: {}".format(msg))

    # Restore the backup to new database mycodo_db_bak
    try:
        app.logger.info("Creating tmp db with restore data")
        command = "influxd restore -portable -db {db} -newdb {dbn} {dir}".format(
            db=mycodo_db, dbn=mycodo_db_backup, dir=tmp_folder)
        app.logger.info("executing '{}'".format(command))
        cmd = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            shell=True)
        cmd_out, cmd_err = cmd.communicate()
        cmd_status = cmd.wait()
        app.logger.info("command output: {}\nErrors: {}\nStatus: {}".format(
            cmd_out.decode('utf-8'), cmd_err, cmd_status))
    except Exception as msg:
        app.logger.info("Error during restore of data to backup db: {}".format(msg))

    # Copy all measurements from backup to current database
    try:
        app.logger.info("Beginning restore of data from tmp db to main db. This could take a while...")
        # dbcon.query("""SELECT * INTO mycodo_stats..:MEASUREMENT FROM /.*/ GROUP BY *""")
        query_str = "SELECT * INTO {}..:MEASUREMENT FROM /.*/ GROUP BY *".format(mycodo_db)
        client.query(query_str)
        app.logger.info("Restore of data from tmp db complete.")
    except Exception as msg:
        app.logger.info("Error during copy of measurements from backup db to production db: {}".format(msg))

    # Delete backup database
    try:
        app.logger.info("Deleting tmp db")
        # dbcon.query('DROP DATABASE "{}"'.format(mycodo_db_backup))
        client.drop_database(mycodo_db_backup)
    except Exception as msg:
        app.logger.info("Error while deleting db after restore: {}".format(msg))

    # Delete tmp directory if it exists
    try:
        app.logger.info("Deleting influxdb restore tmp directory...")
        #shutil.rmtree(tmp_folder)
    except Exception as msg:
        app.logger.info("Error while deleting tmp file directory: {}".format(msg))


def import_influxdb(form_request):
    """
    Receive a zip file containing influx metastore and database that was
    exported with export_influxdb(), then import the metastore and database
    in InfluxDB.
    """
    error = []

    try:
        tmp_folder = os.path.join('/tmp', 'mycodo_influx_tmp')
        full_path = None

        # Save file to upload directory
        filename = form_request.files['file'].filename
        full_path = os.path.join(tmp_folder, filename)
        assure_path_exists(tmp_folder)
        form_request.files['file'].save(os.path.join(tmp_folder, filename))

        # Check if contents of zip file are correct
        try:
            file_list = zipfile.ZipFile(full_path, 'r').namelist()
            if not any(".meta" in s for s in file_list):
                error.append("No '.meta' file found in archive")
            elif not any(".manifest" in s for s in file_list):
                error.append("No '.manifest' file found in archive")
        except Exception as err:
            error.append("Exception while opening zip file: "
                         "{err}".format(err=err))

        if not error:
            # Unzip file
            try:
                zip_ref = zipfile.ZipFile(full_path, 'r')
                zip_ref.extractall(tmp_folder)
                zip_ref.close()
            except Exception as err:
                error.append("Exception while extracting zip file: "
                             "{err}".format(err=err))

        if not error:
            try:
                import_settings_db = threading.Thread(
                    target=thread_import_influxdb,
                    args=(tmp_folder,))
                import_settings_db.start()
                return "success"
            except Exception as err:
                error.append("Exception while importing database: "
                             "{err}".format(err=err))

    except Exception as err:
        error.append("Exception: {}".format(err))

    if error:
        app.logger.error(error)


def cmd_output(command):
    cmd = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    cmd_out, cmd_err = cmd.communicate()
    cmd_status = cmd.wait()
    return cmd_out, cmd_err, cmd_status


def set_user_grp(filepath, user, group):
    """ Set the UID and GUID of a file """
    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(group).gr_gid
    os.chown(filepath, uid, gid)


def assure_path_exists(path):
    """ Create path if it doesn't exist """
    if not os.path.exists(path):
        os.makedirs(path)
        os.chmod(path, 0o774)
        set_user_grp(path, 'pi', 'pi')
    return path


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


def get_ids(data, measurement, time_days):
    """Return a dictionary of user ids sorted based on measurement"""
    number_installed_devices = 0

    # Create dictionary of ID (value) and category (value)
    dict_ids = {}
    for each_data in data['series']:
        if each_data['name'] == measurement:
            try:  # Turn to float if string represents numerical value
                dict_ids[each_data['tags']['anonymous_id']] = float(each_data['values'][0][1])
            except:
                dict_ids[each_data['tags']['anonymous_id']] = each_data['values'][0][1]
            if len(each_data['tags']['anonymous_id']) == 10:
                number_installed_devices += 1

    # Sort lowest to highest by values (measurement)
    sorted_dict_ids = OrderedDict()
    if measurement == 'Mycodo_revision':
        # Sorting version strings (e.g. 7.10.3) doesn't work with sorted()
        inversed_list = []
        for each_key, each_value in dict_ids.items():
            inversed_list.append((each_value, each_key))
        sorted_list = natsort.natsorted(inversed_list)
        for each_set in sorted_list:
            sorted_dict_ids[each_set[1]] = each_set[0]
    else:
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
