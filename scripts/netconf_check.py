#!/usr/bin/env python3
import sys
import json
from ncclient import manager


def print_usage():
    sys.stderr.write(
        "Usage: netconf_check.py[host,port,username,password,operation]\n"
    )


def netconf_hello(host: str, port: int, username: str, password: str) -> str:
    with manager.connect(
        host=host,
        port=port,
        username=username,
        password=password,
        hostkey_verify=False,
        allow_agent=False,
        look_for_keys=False,
        timeout=10,
    ) as m:
        caps = list(m.server_capabilities)
        return json.dumps({"ok": True, "capabilities": caps})


def netconf_get(host: str, port: int, username: str, password: str) -> str:
    with manager.connect(
        host=host,
        port=port,
        username=username,
        password=password,
        hostkey_verify=False,
        allow_agent=False,
        look_for_keys=False,
        timeout=10,
    ) as m:
        reply = m.get().data_xml
        return json.dumps({"ok": True, "len": len(reply)})


def main():
    # Zabbix external checks pass args inside [] separated by commas
    if len(sys.argv) != 2 or not sys.argv[1].startswith("["):
        print_usage()
        sys.exit(1)

    arg_str = sys.argv[1].strip("[]")
    parts = [p.strip() for p in arg_str.split(",")]
    if len(parts) != 5:
        print_usage()
        sys.exit(1)

    host, port_str, username, password, operation = parts
    try:
        port = int(port_str)
    except ValueError:
        sys.stderr.write("Invalid port\n")
        sys.exit(1)

    try:
        if operation == "hello":
            print(netconf_hello(host, port, username, password))
        elif operation == "get":
            print(netconf_get(host, port, username, password))
        else:
            sys.stderr.write("Unknown operation\n")
            sys.exit(1)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(0)


if __name__ == "__main__":
    main()


