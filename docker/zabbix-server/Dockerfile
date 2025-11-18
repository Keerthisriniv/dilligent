FROM zabbix/zabbix-server-pgsql:alpine-6.4-latest

USER root
RUN apk add --no-cache python3 py3-pip openssh-client
RUN pip install --no-cache-dir -r /tmp/requirements.txt || true

# copy requirements first to leverage cache; will be replaced by volume at runtime
COPY ../../scripts/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

USER zabbix


