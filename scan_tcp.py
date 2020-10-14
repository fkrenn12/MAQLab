import socket
import time

def scan_tcp_devices(devices, comlist, comlock):
    deviceidentifications = list(devices.keys())
    idstrings = []
    for d in devices:
        if devices[d]["interface"] == "ethernet":
            idstrings.append(devices[d]["cmd_idn"].encode("utf-8"))
    idstrings = list(set(idstrings))
    print(idstrings)
    while True:
        time.sleep(1)
        # print("Scan ethernet ip...")



