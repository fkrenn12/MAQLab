import threading
from scan_tcp import scan_tcp_devices
import json

# TODO: loading the configurations should be done via mqtt also
with open('config/inventory.json') as json_file:
    inventar = json.load(json_file)
    inventarnumbers = list(inventar.keys())
    # print("Inventarumbers:")
    # print(inventarnumbers)

with open('config/devices.json') as json_file:
    devices = json.load(json_file)
    deviceidentifications = list(devices.keys())
    print("Devices:")
    print(devices)
    print("Deviceidentifications:")
    print(deviceidentifications)
    ld = []
    for d in devices:
        ld.append(devices[d]["cmd_idn"])
        # print(devices[d]["cmd_idn"])
    ld = set(ld)
    # print(ld)

devlist = []
iplist = []
devlock = threading.Lock()
etherlock = threading.Lock()

thread_detect_ethernet = threading.Thread(target=scan_tcp_devices, args=(devices, iplist, etherlock,))
thread_detect_ethernet.start()
