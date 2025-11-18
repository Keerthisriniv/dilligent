Real-Time Healthcare IoT Network Monitoring (Ubuntu)

Overview

This project deploys an open-source Network Management System (NMS) for hospital IoT networks using Zabbix, with SNMP and NETCONF integrations, an alarm lifecycle service, and observability dashboards in Grafana.

Stack

- Zabbix Server + Web UI (PostgreSQL backend)
- SNMP polling via Zabbix (for networked medical devices that support SNMP)
- NETCONF checks via Zabbix external scripts (ncclient)
- Alarm Lifecycle API (FastAPI) for acknowledge/resolve workflows
- Grafana with Zabbix plugin, pre-provisioned datasource and dashboards

Goals

- Improved uptime and patient safety through proactive monitoring and alerting
- Zero-downtime posture via alerting, escalation, and observability

Prerequisites (Ubuntu)

- Ubuntu 22.04+ host with internet access
- Docker and Docker Compose installed
- Open ports: 80/443 (Grafana/Zabbix Web), 10051 (Zabbix Server), 162/UDP (optional SNMP traps)

Quick Start

1) Install Docker and Compose on Ubuntu

```bash
sudo bash scripts/install_docker_ubuntu.sh
```

2) Start the stack

```bash
docker compose up -d
```

3) Access UIs

- Zabbix Web: http://localhost:8080 (default user: Admin / zabbix)
- Grafana: http://localhost:3000 (default user: admin / admin)

4) Add devices

- SNMP: ensure devices have SNMP enabled (v2c or v3). Use the Ansible playbook to enable SNMP on Ubuntu endpoints.
- NETCONF: configure network devices for NETCONF over SSH and add corresponding Zabbix items using the external script `netconf_check.py`.

Repository Layout

```
docker-compose.yml
docker/
  zabbix-server/
    Dockerfile
scripts/
  install_docker_ubuntu.sh
  netconf_check.py
  requirements.txt
grafana/
  provisioning/
    datasources/
      zabbix.yml
    dashboards/
      dashboards.json
services/
  alarm-lifecycle/
    Dockerfile
    requirements.txt
    main.py
ansible/
  inventory.ini
  playbooks/
    enable_snmp.yml
zabbix/
  templates/
    README.md
```

SNMP on Ubuntu Hosts

Use Ansible to enable SNMP daemon on Ubuntu endpoints:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/enable_snmp.yml --become
```

NETCONF Checks

Zabbix runs `scripts/netconf_check.py` as an external script to test NETCONF availability and basic RPCs using `ncclient`. Example Zabbix item (External check):

Parameter format:

```
netconf_check.py[host,830,username,password,hello]
```

Dashboards

Grafana is pre-provisioned with the Zabbix datasource and a starter dashboard. Import additional dashboards or expand as needed.

Alarm Lifecycle API

The FastAPI service provides a minimal alarm acknowledge/resolve workflow, suitable for webhooks or Zabbix actions.

Security Notes

- Replace default passwords and secrets.
- Use HTTPS and restricted networks for production.
- Consider SNMPv3 for secure SNMP.
- Use SSH keys for NETCONF.

License

MIT


"# Healthcare-monitoring" 
