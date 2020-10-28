'''

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
'''

import platform
import time
import paho.mqtt.client as paho
import threading
import json
import secrets

from scan_tcp import scan_tcp_devices

from Extensions.Manson_NTP6531 import NTP6531
from Extensions.BKPrecision_2831E import BK2831E
from Extensions.Keithley_SM2400 import SM2400

inventory = None
inventory_numbers = None
devices = None
deviceidentifications = None

devlist = []
iplist = []
devlock = threading.Lock()
etherlock = threading.Lock()

FILENAME_CONFIG_DEVICES = "devices.json"
FILENAME_CONFIG_INVENTORY = "inventory.json"
PATHNAME_CONFIG_DEVICES = "/config/" + FILENAME_CONFIG_DEVICES
PATHNAME_CONFIG_INVENTORY = "/config/" + FILENAME_CONFIG_INVENTORY
session_id = secrets.token_urlsafe(5)


# --------------------------------------------------------
# MQTT Broker callbacks
# --------------------------------------------------------
def mqttloop(_client):
    _client.loop_forever()


def on_connect(_client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT-Broker.")
        _client.subscribe("maqlab/cmd/#", qos=0)
        _client.subscribe("maqlab/+/cmd/#", qos=0)
        _client.subscribe("maqlab/rep/file/#", qos=0)
        _client.subscribe("maqlab/+/rep/file/#", qos=0)


def on_disconnect(_client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")
    # server.stop()
    # server.start()
    _client.reconnect()


def on_message(_client, _userdata, _msg):
    global devlist
    global devlock
    global inventory
    global inventory_numbers
    global devices
    global deviceidentifications

    # check topic
    if isinstance(_msg.topic, bytes):
        topic = _msg.topic.decode("utf-8")
    elif isinstance(_msg.topic, str):
        topic = _msg.topic
    else:
        return

    if "/rep/file/" in topic:
        if FILENAME_CONFIG_DEVICES in topic:
            with devlock:
                try:
                    deviceidentifications = []
                    devices = json.loads(_msg.payload.decode("utf-8"))
                    for i in devices:
                        deviceidentifications.append(i["device"])
                    # print("Device-Identifiers:" + str(deviceidentifications))
                except:
                    print("Error in devices.json")
                    return
        elif FILENAME_CONFIG_INVENTORY in topic:
            with devlock:
                try:
                    inventory_numbers = []
                    inventory = json.loads(_msg.payload.decode("utf-8"))
                    for i in inventory:
                        inventory_numbers.append(i["inventar_number"])
                    # print("Inventory numbers:" + str(inventory_numbers))
                except:
                    print("Error in inventory.json")
                    return
        return

    # loaded configuration must be done before any
    # messages can be distributed
    if devices is None or inventory is None:
        return

    # print(topic, _msg.payload)
    with devlock:
        if len(devlist) > 0:
            # distribute message to all devices
            for _dev in devlist:
                try:
                    _dev.mqttmessage(_client, _msg)
                except:
                    pass


if __name__ == "__main__":
    print("MAQlab - serial node started.")
    client = paho.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.username_pw_set("maqlab", "maqlab")
    client.connect("techfit.at", 1883)

    thread_mqttloop = threading.Thread(target=mqttloop, args=(client,))
    thread_mqttloop.start()

    time.sleep(1)
    print("Request configuration files...")
    client.publish("maqlab/" + session_id + "/cmd/file/get", PATHNAME_CONFIG_DEVICES)
    time.sleep(0.05)
    client.publish("maqlab/" + session_id + "/cmd/file/get", PATHNAME_CONFIG_INVENTORY)

    # wait for data from mqtt file server
    while True:
        time.sleep(0.1)
        with devlock:
            if devices is not None and inventory is not None:
                break

    print("Configuration files received.")
    thread_detect_ethernet = threading.Thread(target=scan_tcp_devices, args=(devices, iplist, etherlock,))
    thread_detect_ethernet.start()

    while True:
        # ----------------------------------------------------------------------------------
        # Stepping through the list and generate the device instance from the classname
        # ----------------------------------------------------------------------------------
        with etherlock:
            time.sleep(0.1)
            if len(iplist) > 0:
                for ip in iplist:
                    # print(com)
                    for dev in devices:
                        devobject = None
                        # print(d)
                        # print(devices[d]["classname"])
                        dclassname = dev["classname"]
                        if dclassname in ip:
                            # generating a deviceclass from classname
                            devobject = globals()[dclassname](ip[dclassname])
                        if devobject is not None:
                            # search for inventarnumber of the device with spec serialnumber
                            # there are some devices not declared with a serialnumber
                            # so we have to use the random generated serial for the inventarnumber
                            inventory_number = '0'

                            if inventory is not None:
                                for devi in inventory:
                                    if devi["serial"] == devobject.serialnumber:
                                        inventory_number = devi["inventar_number"]
                                        break

                            if inventory_number == '0':
                                inventory_number = devobject.serialnumber

                            with devlock:
                                devlist.append(devobject)
                                devobject.on_created(ip[dclassname], inventory_number)

                iplist.clear()
        # --------------------------------------------------------------------------
        time.sleep(0.02)

        # --------------------------------------------------------------------------
        # Step through connected devices and call the handlers
        # --------------------------------------------------------------------------

        if len(devlist) > 0:
            for dev in devlist:
                if dev.connected():
                    # print("Connected")
                    dev.execute()
                else:
                    # print("NOT Connected")
                    with devlock:
                        dev.on_destroyed()
                        devlist.remove(dev)
                        del dev
