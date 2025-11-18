#!/usr/bin/env bash
set -euo pipefail

# This script installs Zabbix Server + Web (Apache, PHP) with PostgreSQL,
# Grafana with Zabbix plugin, configures Zabbix external scripts path,
# installs Python deps for NETCONF checks, and installs the Alarm Lifecycle API
# as a systemd service. Tested on Ubuntu 22.04/24.04.

if [[ $(id -u) -ne 0 ]]; then
  echo "Please run as root (sudo)." >&2
  exit 1
fi

ZBX_DB=zabbix
ZBX_DB_USER=zabbix
ZBX_DB_PASS=zabbix
REPO_ROOT="$(cd "$(dirname "$0")"/.. && pwd)"

echo "[1/8] Installing base packages..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql postgresql-contrib \
  apt-transport-https ca-certificates curl gnupg lsb-release \
  python3 python3-venv python3-pip

echo "[2/8] Setting up PostgreSQL for Zabbix..."
systemctl enable --now postgresql
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${ZBX_DB}'" | grep -q 1 || \
  sudo -u postgres createdb ${ZBX_DB}
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${ZBX_DB_USER}'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE USER ${ZBX_DB_USER} WITH PASSWORD '${ZBX_DB_PASS}';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${ZBX_DB} TO ${ZBX_DB_USER};"

echo "[3/8] Installing Zabbix repository and packages..."
CODENAME=$(. /etc/os-release; echo ${VERSION_CODENAME})
KEYRING=/usr/share/keyrings/zabbix-official-repo.gpg
curl -fsSL https://repo.zabbix.com/zabbix-official-repo.key | gpg --dearmor -o ${KEYRING}
chmod 644 ${KEYRING}
echo "deb [signed-by=${KEYRING}] https://repo.zabbix.com/zabbix/7.0/ubuntu/ ${CODENAME} main" \
  > /etc/apt/sources.list.d/zabbix.list
if ! apt-get update; then
  # Fallback to jammy repository on noble
  echo "deb [signed-by=${KEYRING}] https://repo.zabbix.com/zabbix/7.0/ubuntu/ jammy main" \
    > /etc/apt/sources.list.d/zabbix.list
  apt-get update
fi
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  zabbix-server-pgsql zabbix-frontend-php zabbix-apache-conf zabbix-sql-scripts zabbix-agent

echo "[4/8] Initializing Zabbix database schema..."
sudo -u postgres psql -d ${ZBX_DB} -tc "SELECT tablename FROM pg_tables WHERE schemaname='public' LIMIT 1;" | grep -q . || {
  zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u postgres psql ${ZBX_DB}
}

echo "[5/8] Configuring Zabbix server DB connection..."
sed -i "s/^# DBPassword=.*/DBPassword=${ZBX_DB_PASS}/" /etc/zabbix/zabbix_server.conf
sed -i "s/^# DBUser=.*/DBUser=${ZBX_DB_USER}/" /etc/zabbix/zabbix_server.conf
sed -i "s/^# DBName=.*/DBName=${ZBX_DB}/" /etc/zabbix/zabbix_server.conf

echo "[6/8] Installing Grafana and Zabbix plugin..."
mkdir -p /etc/apt/keyrings
curl -fsSL https://packages.grafana.com/gpg.key | gpg --dearmor -o /etc/apt/keyrings/grafana.gpg
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://packages.grafana.com/oss/deb stable main" \
  > /etc/apt/sources.list.d/grafana.list
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y grafana
/usr/sbin/grafana-cli plugins install alexanderzobnin-zabbix-app || true
systemctl enable grafana-server

echo "[7/8] Installing NETCONF deps and external script..."
EXT_VENV=/opt/zabbix-ext
python3 -m venv ${EXT_VENV}
${EXT_VENV}/bin/pip install --no-cache-dir -r "${REPO_ROOT}/scripts/requirements.txt"
install -d -o zabbix -g zabbix /usr/lib/zabbix/externalscripts
install -m 0755 "${REPO_ROOT}/scripts/netconf_check.py" /usr/lib/zabbix/externalscripts/netconf_check.py
sed -i "1s|.*|#!${EXT_VENV}/bin/python|" /usr/lib/zabbix/externalscripts/netconf_check.py

echo "[8/8] Installing Alarm Lifecycle API (systemd service)..."
APP_DIR=/opt/alarm-lifecycle
install -d ${APP_DIR}
cp "${REPO_ROOT}/services/alarm-lifecycle/main.py" ${APP_DIR}/main.py
cp "${REPO_ROOT}/services/alarm-lifecycle/requirements.txt" ${APP_DIR}/requirements.txt
python3 -m venv ${APP_DIR}/.venv
${APP_DIR}/.venv/bin/pip install --no-cache-dir -r ${APP_DIR}/requirements.txt
cp "${REPO_ROOT}/services/alarm-lifecycle/alarm-lifecycle.service" /etc/systemd/system/alarm-lifecycle.service
systemctl daemon-reload
systemctl enable alarm-lifecycle

echo "Starting services..."
systemctl restart zabbix-server zabbix-agent apache2 grafana-server alarm-lifecycle || true

echo "Done. Access Zabbix Web at http://<host>/zabbix and Grafana at http://<host>:3000"


