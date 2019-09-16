#!/bin/bash
#
# Install with:
# sudo /bin/bash ./install.sh

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd -P )

pip install virtualenv --upgrade
virtualenv --system-site-packages -p python3 ${INSTALL_DIRECTORY}/env
${INSTALL_DIRECTORY}/env/bin/pip3 install --upgrade pip setuptools
${INSTALL_DIRECTORY}/env/bin/pip3 install --upgrade -r ~/mycodo_stats_viewer/requirements.txt

influx -execute "CREATE DATABASE mycodo_stats" &&
influx -execute "CREATE USER mycodo_stats WITH PASSWORD 'Io8Nasr5JJDdhPOj32222'" &&
influx -execute "GRANT WRITE ON mycodo_stats TO mycodo_stats" &&

systemctl disable mycodostats.service
systemctl enable ${INSTALL_DIRECTORY}/mycodostats.service
