import asyncio
import datetime
import json
import secrets

import paho.mqtt.client as paho

from scan_serial import scan_serial_devices
from scan_tcp import scan_tcp_devices

from Extensions.Manson_NTP6531 import NTP6531
from Extensions.BKPrecision_2831E import BK2831E
from Extensions.Keithley_SM2400 import SM2400
from Extensions.Delta_SM70AR24 import SM70AR24
from Extensions.Fluke_NORMA4000 import NORMA4000

client = paho.Client()
inventory = None
inventory_numbers = None
devices = []
deviceidentifications = None
idstrings = {}

devlist = []
comlist = []
iplist = []
addresses = []

FILENAME_CONFIG_DEVICES = "devices.json"
FILENAME_CONFIG_INVENTORY = "inventory.json"
PATHNAME_CONFIG_DEVICES = "/config/" + FILENAME_CONFIG_DEVICES
PATHNAME_CONFIG_INVENTORY = "/config/" + FILENAME_CONFIG_INVENTORY
session_id = secrets.token_urlsafe(5)


# --------------------------------------------------------
# MQTT Broker callbacks
# --------------------------------------------------------
def on_connect(_client, userdata, flags, rc):
    if rc == 0:
        print(str(datetime.datetime.now()) + "  :" + "Connected to MQTT-Broker.")
        _client.subscribe("maqlab/cmd/#", qos=0)
        _client.subscribe("maqlab/+/cmd/#", qos=0)
        _client.subscribe("maqlab/rep/file/#", qos=0)
        _client.subscribe("maqlab/+/rep/file/#", qos=0)


def on_disconnect(_client, userdata, rc):
    if rc != 0:
        print(str(datetime.datetime.now()) + "  :" + "Unexpected disconnection.")
    # server.stop()
    # server.start()
    _client.reconnect()


def on_message(_client, _userdata, _msg):
    global devlist
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

    # configuration file repeated
    if "/rep/file/" in topic:
        if FILENAME_CONFIG_DEVICES in topic:
            try:
                deviceidentifications = []
                devices = json.loads(_msg.payload.decode("utf-8"))
                for i in devices:
                    deviceidentifications.append(i["device"])
                # print("Device-Identifiers:" + str(deviceidentifications))
            except Exception as e:
                print(devices)
                print(str(datetime.datetime.now()) + "  :" + "Error in devices.json")
                print(e)
                return
        elif FILENAME_CONFIG_INVENTORY in topic:
            try:
                inventory_numbers = []
                inventory = json.loads(_msg.payload.decode("utf-8"))
                for i in inventory:
                    inventory_numbers.append(i["inventar_number"])
                # print("Inventory numbers:" + str(inventory_numbers))
            except Exception as e:
                print(inventory)
                print(str(datetime.datetime.now()) + "  :" + "Error in inventory.json")
                print(e)
                return
        return

    # loaded configuration must be done before any
    # messages can be distributed
    if devices is None or inventory is None:
        return

    # print(topic, _msg.payload)

    if len(devlist) > 0:
        # distribute message to all devices
        for _dev in devlist:
            try:
                _dev.mqttmessage(_client, _msg)
            except:
                pass


async def mqttloop(_client):
    while True:
        if _client is not None:
            _client.loop(0.0001)
        await asyncio.sleep(0.05)


async def tcp_generate_classes():
    while True:
        # ----------------------------------------------------------------------------------
        # Stepping through the list and generate the device instance from the classname
        # ----------------------------------------------------------------------------------
        await asyncio.sleep(0.2)
        try:
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

                            devlist.append(devobject)
                            devobject.on_created(ip[dclassname], inventory_number)
                await asyncio.sleep(0.5)  # be cooperative !
                iplist.clear()
        except:
            pass


async def serial_generate_classes():
    while True:
        await asyncio.sleep(0.2)
        try:
            # ----------------------------------------------------------------------------------
            # Stepping through the COM list and generate the device instance from the classname
            # ----------------------------------------------------------------------------------
            if len(comlist) > 0:
                for com in comlist:
                    # print(com)
                    for dev in devices:
                        devobject = None
                        # print(d)
                        # print(devices[d]["classname"])
                        dclassname = dev["classname"]
                        if dclassname in com:
                            # generating a deviceclass from classname
                            devobject = globals()[dclassname](com[dclassname])
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

                            devlist.append(devobject)
                            devobject.on_created(com[dclassname], inventory_number)
                await asyncio.sleep(0.5)  # be cooperative !
                comlist.clear()
        except:
            pass


async def execution_loop():
    # --------------------------------------------------------------------------
    # Step through connected devices and call the handlers
    # --------------------------------------------------------------------------
    while True:
        await asyncio.sleep(0.05)
        if len(devlist) > 0:
            for dev in devlist:
                if dev.connected():
                    # print("Connected")
                    dev.execute()
                else:
                    # print("NOT Connected")
                    dev.on_destroyed()
                    devlist.remove(dev)
                    del dev


async def connector(event_config_readed):
    global client
    global idstrings
    print(str(datetime.datetime.now()) + "  :" + "MAQlab - N O D E started")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.username_pw_set("maqlab", "maqlab")
    client.connect("techfit.at", 1883)
    while not client.is_connected():
        await asyncio.sleep(0.05)
    print(str(datetime.datetime.now()) + "  :" + "Requesting configuration files...")
    client.publish("maqlab/" + session_id + "/cmd/file/get", PATHNAME_CONFIG_DEVICES)
    client.publish("maqlab/" + session_id + "/cmd/file/get", PATHNAME_CONFIG_INVENTORY)
    # Waiting for data from mqtt file server
    # First we need the configuration files
    # Therefore we wait for it
    while True:
        await asyncio.sleep(0.2)
        if len(devices) > 0 and inventory is not None:
            break
        print(str(datetime.datetime.now()) + "  :" + "Wait for configuration files...")

    print(str(datetime.datetime.now()) + "  :" + "Configuration files received.")

    idstrings_ethernet = list()
    idstrings_serial = list()
    for d in devices:
        idstring = d["cmd_idn"]
        idstring = idstring.replace("<CR>", "\r")
        idstring = idstring.replace("<LF>", "\n")
        if d["interface"] == "ethernet":
            idstrings_ethernet.append(idstring.encode("utf-8"))
        elif d["interface"] == "usb-vcom":
            idstrings_serial.append(idstring.encode("utf-8"))

    idstrings = {"ethernet": list(set(idstrings_ethernet)), "serial": list(set(idstrings_serial))}
    for invent in inventory:
        # print(invent)
        try:
            # addr = (invent["ipaddress"], invent["port]"])
            addr = (invent["ipaddress"], int(invent["port"]))
            addresses.append(addr)
        except:
            pass
    event_config_readed.set()


async def main():
    event_config_readed = asyncio.Event()
    # create tasks
    global client
    task1 = loop.create_task(mqttloop(client))
    task2 = loop.create_task(connector(event_config_readed))
    await event_config_readed.wait()
    task3 = loop.create_task(serial_generate_classes())
    task4 = loop.create_task(tcp_generate_classes())
    task5 = loop.create_task(scan_serial_devices(devices, comlist))
    task6 = loop.create_task(scan_tcp_devices(devices, addresses, iplist))
    task7 = loop.create_task(execution_loop())
    # wait until all tasks finished
    # await asyncio.wait([task1, task2, task3, task5, task7])
    await asyncio.wait([task1, task2, task3, task4, task5, task6, task7])
    # but will never happen in real !!!


if __name__ == "__main__":
    # Declare event loop
    loop = asyncio.get_event_loop()
    # Run the code until completing all task
    loop.run_until_complete(main())
    # Close the loop
    loop.close()