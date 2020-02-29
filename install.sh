#!/bin/bash
#
# Install Mycodo first, then execute:
# sudo /bin/bash ./install.sh
#
# Backup database:
# mkdir ~/backup_mycodo_stats
# influxd backup -portable -database mycodo_stats ~/backup_mycodo_stats
#
# Restore database:
# influxd restore -portable -db mycodo_stats -newdb mycodo_stats_bak ~/backup_mycodo_stats
# influx
# USE mycodo_stats_bak
# SELECT * INTO mycodo_stats..:MEASUREMENT FROM /.*/ GROUP BY *
#
# If this SELECT command times out, you may need to copy data in batches, based on time. For example:
# SELECT * INTO mycodo_stats..:MEASUREMENT FROM /.*/ WHERE time < '2019-01-01T00:00:00Z' GROUP BY *
# SELECT * INTO mycodo_stats..:MEASUREMENT FROM /.*/ WHERE time > '2019-01-01T00:00:00Z' AND time < '2019-03-01T00:00:00Z' GROUP BY *
# Do this for several time periods until all data is copied.
#
# DROP DATABASE mycodo_stats_bak

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd -P )

pip install virtualenv --upgrade
virtualenv --system-site-packages -p python3 "${INSTALL_DIRECTORY}"/env
"${INSTALL_DIRECTORY}"/env/bin/pip3 install --upgrade pip setuptools
"${INSTALL_DIRECTORY}"/env/bin/pip3 install --upgrade -r "${INSTALL_DIRECTORY}"/requirements.txt

influx -execute "CREATE DATABASE mycodo_stats" &&
influx -execute "CREATE USER mycodo_stats WITH PASSWORD 'Io8Nasr5JJDdhPOj32222'" &&
influx -execute "GRANT WRITE ON mycodo_stats TO mycodo_stats" &&

systemctl disable mycodostats.service
systemctl enable "${INSTALL_DIRECTORY}"/mycodostats.service
