import asyncio
import datetime
import json
import secrets
import external_modules.subpub.subpub as subpub
from external_modules.configobj import ConfigObj
import paho.mqtt.client as paho
import os
from scan_serial import scan_serial_devices
from scan_tcp import scan_tcp_devices
import glob
import importlib
import sys
import project_utils
import psutil

if "python.exe" not in psutil.Process(os.getpid()).name():
    execute_mode = "exe"
else:
    execute_mode = "script"

# deletes _meixxxx files from previous python starts-
# Without deleting the files, disk memory consumption will
# increase without any notice from the user
if execute_mode == "exe":
    project_utils.cleanup_mei()

print(os.path.dirname(os.path.realpath(__file__)))
print(sys.path.append(os.path.dirname(sys.executable)))
dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir)
# x = input()
for path in sys.path:
    print(path)

# exec("from Extensions.Manson_NTP6531 import NTP6531")

'''
try:
    exec("import Extensions", globals())
    exec("from Extensions import BKPrecision_2831E as BK")
    exec("from Extensions import Manson_NTP6531 as NTP6531", globals())
except Exception as e:
    print(e)
    # x = input()
'''
'''
try:
    exec("from Extensions.BKPrecision_2831E import BK2831E", globals())
except Exception as e:
    print(e)
    # x = input()
'''
'''
try:
    importlib.import_module("Extensions")
    from Extensions import BKPrecision_2831E as BK

    from Extensions import Manson_NTP6531 as NTP6531
except Exception as e:
    print(e)
'''

from Extensions.Manson_NTP6531 import NTP6531
from Extensions.BKPrecision_2831E import BK2831E
from Extensions.Delta_SM70AR24 import SM70AR24
from Extensions.Fluke_NORMA4000 import NORMA4000
from Extensions.Keithley_SM2400 import SM2400
from Extensions.BKPrecision_2831E import BK2831E
# x = input()
sp = subpub.SubPub()
mqtt_device_reply = sp.subscribe("maqlab(.+)/rep/(.+)$")

client = paho.Client()
inventory = None
inventory_numbers = None
devices = list()
deviceidentifications = None
config_maqlab = None
config_devices = list()
config_devices_names = list()
idstrings = {}

devlist = []
comlist = []
iplist = []
addresses = []
mqtt_subscriptions = list()

MQTT_HOST = "techfit.at"
MQTT_PORT = 1883
MQTT_USER = "maqlab"
MQTT_PASSWORD = "maqlab"
MQTT_ROOT = "maqlab/"

FILENAME_CONFIG_DEVICES = "devices.json"
FILENAME_CONFIG_INVENTORY = "inventory.json"
PATHNAME_CONFIG_DEVICES = "/config/" + FILENAME_CONFIG_DEVICES
PATHNAME_CONFIG_INVENTORY = "/config/" + FILENAME_CONFIG_INVENTORY
session_id = secrets.token_urlsafe(3)


'''
config_files = glob.glob(os.path.dirname(os.path.abspath(__file__)) + "/**/*.conf", recursive=True)
# NTP6531 = importlib.import_module("Extensions.Manson_NTP6531")
print(config_files)

for file in config_files:
    filename_without_extension = os.path.splitext(os.path.basename(file))[0].lower()
    if filename_without_extension == "maqlab":
        config_maqlab = ConfigObj(file)  # prepared for future use
    else:
        cfg = ConfigObj(file)  # prepared for future use
        name = str(cfg["GENERAL"]["device"]).lower()
        if filename_without_extension == name:
            # this is a device configuration file
            config_devices.append(cfg)
            config_devices_names.append(name)
'''
'''
# import modules
imports = config_maqlab["IMPORTS"]
print(imports)
for x in imports:
    print(imports[x])
    exec(imports[x])
'''

# --------------------------------------------------------
# MQTT Broker callbacks
# --------------------------------------------------------
def on_connect(_client, userdata, flags, rc):
    if rc == 0:
        print(str(datetime.datetime.now()) + "  :" + "Connected to MQTT-Broker")
        for subscription in mqtt_subscriptions:
            _client.subscribe(subscription)


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
def on_disconnect(_client, userdata, rc):
    if rc != 0:
        print(str(datetime.datetime.now()) + "  :" + "Disconnected from MQTT-Broker")
    try:
        _client.disconnect()
    except:
        pass


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
def on_message(_client, _userdata, _msg):
    global sp
    global devlist
    global inventory
    global inventory_numbers
    global devices
    global deviceidentifications

    try:
        topic = _msg.topic.decode("utf-8")
    except:
        pass
    topic = _msg.topic

    # print(topic, _msg.payload)
    try:
        # configuration file repeated
        if "/rep/file/" in topic:
            if FILENAME_CONFIG_DEVICES in topic:
                try:
                    devices = json.loads(_msg.payload.decode("utf-8"))
                    deviceidentifications = list()
                    for i in devices:
                        deviceidentifications.append(i["device"])
                    # print("Device-Identifiers:" + str(deviceidentifications))
                except Exception as e:
                    # print(devices)
                    print(str(datetime.datetime.now()) + "  :" + "Error in devices.json")
                    # print(e)
                    return
            elif FILENAME_CONFIG_INVENTORY in topic:
                try:
                    inventory = json.loads(_msg.payload.decode("utf-8"))
                    inventory_numbers = list()
                    for i in inventory:
                        inventory_numbers.append(i["inventar_number"])
                    # print("Inventory numbers:" + str(inventory_numbers))
                except Exception as e:
                    # print(inventory)
                    print(str(datetime.datetime.now()) + "  :" + "Error in inventory.json")
                    # print(e)
                    return
            return
    except:
        pass

    # loaded configuration must be done before any
    # messages can be distributed
    if devices is None or inventory is None:
        return

    sp.publish(topic, _msg.payload)


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
async def mqttloop(_client):
    while True:
        try:
            _client.loop(0.001)
        except:
            pass
        await asyncio.sleep(0.01)

        # check the reply queues from the devices
        # and send messages to the MQTT-broker
        if not mqtt_device_reply.empty():
            match, data = mqtt_device_reply.get()
            _client.publish(match.string, data)


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
async def tcp_generate_classes():
    global mqtt_subscriptions
    global sp
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
                            devobject.on_created(ip[dclassname], inventory_number, sp)
                            # starting the thread
                            devobject.start()
                            try:
                                subscription = ("maqlab/+/cmd/" + str(devobject.accessnumber) + "/#", 0)
                                mqtt_subscriptions.append(subscription)
                                client.subscribe(subscription)

                                subscription = ("maqlab/+/+/cmd/" + str(devobject.accessnumber) + "/#", 0)
                                mqtt_subscriptions.append(subscription)
                                client.subscribe(subscription)

                                mqtt_subscriptions = list(set(mqtt_subscriptions))

                            except:
                                raise
                            # --------------------------------------------------------------------> Subscribe
                await asyncio.sleep(0.5)  # be cooperative !
                iplist.clear()
        except:
            raise


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
async def serial_generate_classes():
    global mqtt_subscriptions
    global sp
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
                            # search for inventarnumber of the device with spec serialnumyber
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

                            # --------------------------------------------------------
                            #
                            # --------------------------------------------------------
                            devlist.append(devobject)

                            devobject.on_created(com[dclassname], inventory_number, sp)
                            # starting the thread
                            devobject.start()
                            # --------------------------------------------------------------------> Subscribe
                            try:
                                subscription = ("maqlab/+/cmd/" + str(devobject.accessnumber) + "/#", 0)
                                mqtt_subscriptions.append(subscription)
                                client.subscribe(subscription)

                                subscription = ("maqlab/+/+/cmd/" + str(devobject.accessnumber) + "/#", 0)
                                mqtt_subscriptions.append(subscription)
                                client.subscribe(subscription)

                                mqtt_subscriptions = list(set(mqtt_subscriptions))

                            except:
                                raise
                await asyncio.sleep(0.5)  # be cooperative !
                comlist.clear()
        except:
            raise


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
async def remove_loop():
    # --------------------------------------------------------------------------
    # Step through connected devices and check the threads stopped
    # --------------------------------------------------------------------------
    while True:
        await asyncio.sleep(0.2)
        # we catch all exceptions to avoid loop termination in any case
        try:
            # step through all devices
            for dev in devlist:
                # check the thread is stopped already
                if not dev.is_alive():
                    # Unsubscribing from mqtt-client and removing from internal list
                    try:
                        subscription = ("maqlab/+/cmd/" + str(dev.accessnumber) + "/#", 0)
                        mqtt_subscriptions.remove(subscription)
                        client.unsubscribe(subscription[0])
                    except:
                        pass

                    try:
                        subscription = ("maqlab/+/+/cmd/" + str(dev.accessnumber) + "/#", 0)
                        mqtt_subscriptions.remove(subscription)
                        client.unsubscribe(subscription[0])
                    except:
                        pass
                    try:
                        # remove from list
                        devlist.remove(dev)
                    except:
                        pass
                    # last call to the device
                    dev.on_destroyed()
                    # destroy the object
                    del dev
        except:
            pass


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
async def connector(event_config_readed):
    global client
    global idstrings

    print(str(datetime.datetime.now()) + "  :" + "M A Q L A B  - Node started")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_subscriptions.append(("maqlab/cmd/?", 0))
    mqtt_subscriptions.append(("maqlab/+/cmd/?", 0))
    mqtt_subscriptions.append(("maqlab/+/+/cmd/?", 0))
    mqtt_subscriptions.append(("maqlab/" + session_id + "/rep/file/#", 0))

    while True:
        # we are looping the connect
        # because we also need DNS
        while True:
            try:
                client.connect(MQTT_HOST, MQTT_PORT)
                break
            except:
                print(str(datetime.datetime.now()) + "  :" + "Probably not connected to the Internet")
                await asyncio.sleep(5)

        while not client.is_connected():
            await asyncio.sleep(0.05)
        print(str(datetime.datetime.now()) + "  :" + "Requesting configuration files")
        client.publish(MQTT_ROOT + session_id + "/cmd/file/get", PATHNAME_CONFIG_DEVICES)
        client.publish(MQTT_ROOT + session_id + "/cmd/file/get", PATHNAME_CONFIG_INVENTORY)
        # Waiting for data from mqtt file server
        # First we need the configuration files
        # Therefore we wait for it
        while True:
            await asyncio.sleep(0.2)
            if len(devices) > 0 and inventory is not None:
                break
            print(str(datetime.datetime.now()) + "  :" + "Waiting for configuration files")

        print(str(datetime.datetime.now()) + "  :" + "Configuration files received")

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

        # continue checking the connection in a loop
        try:
            while client.is_connected():
                await asyncio.sleep(1)
        except:
            pass
        # disconnection detected
        # we are forcing to disconnect from our side
        # as a second action, to get sure to be disconnected
        client.disconnect()


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
async def main():
    event_config_readed = asyncio.Event()
    event_connection_lost = asyncio.Event()
    # create tasks
    global client
    task1 = loop.create_task(mqttloop(client))
    task2 = loop.create_task(connector(event_config_readed))
    await event_config_readed.wait()

    if serial_scan == "y":
        task3 = loop.create_task(serial_generate_classes())
        task5 = loop.create_task(scan_serial_devices(devices, comlist))

    if tcp_scan == "y":
        task4 = loop.create_task(tcp_generate_classes())
        task6 = loop.create_task(scan_tcp_devices(devices, addresses, iplist))

    task7 = loop.create_task(remove_loop())
    # wait until all tasks finished
    await asyncio.wait([task1])
    # but will never happen in real !!!


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n")
    serial_scan = 'y'
    tcp_scan = 'n'
    '''
    serial_scan = input("For serial scan, press enter or any key with enter, other wise 'n' :")
    if serial_scan != 'n':
        serial_scan = 'y'

    tcp_scan = input("For tcp scan, press enter or any key with enter, other wise 'n' :")
    if tcp_scan != 'n':
        tcp_scan = 'y'

    if serial_scan == 'y':
        print("\nSerial scan: YES")
    else:
        print("\nSerial scan: NO")

    if tcp_scan == 'y':
        print("TCP scan: YES")
    else:
        print("TCP scan: NO")

    print("\n")
    '''
    # Declare event loop
    loop = asyncio.get_event_loop()
    # Run the code until completing all task
    loop.run_until_complete(main())
    # Close the loop
    loop.close()
