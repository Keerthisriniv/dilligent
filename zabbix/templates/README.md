Zabbix Templates

- Import custom templates here (XML/JSON) for SNMP devices and NETCONF checks.
- Create items:
  - SNMP: sysUpTime, ifOperStatus, device-specific OIDs.
  - NETCONF: External check `netconf_check.py["{HOST.IP}",830,user,pass,hello]` returning capabilities.
- Add triggers for critical metrics (link down, high CPU/mem, NETCONF not reachable).


