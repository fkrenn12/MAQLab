import platform
import time
import paho.mqtt.client as paho
import threading
import json
from sshtunnel import SSHTunnelForwarder

from serial_scan import scan_serial_devices
from ethernet_scan import scan_ethernet_devices
from Manson_NTP6531_extension import NTP6531
from BKPrecision_2831E_extension import BK2831E
from Keithley_SM2400_extension import SM2400

p = platform.platform()
if "Windows" in p:
    this_os = "Windows"
else:
    this_os = "Linux"

with open('config/inventar.json') as json_file:
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

# print(inventarnumbers)
# print(deviceidentifications)

devlist = []
comlist = []
iplist = []
devlock = threading.Lock()
comlock = threading.Lock()
etherlock = threading.Lock()


# exit(0)







# --------------------------------------------------------
# MQTT Broker callbacks
# --------------------------------------------------------
def mqttloop(_client):
    _client.loop_forever()


def on_connect(_client, userdata, flags, rc):
    # print("CONNACK received with code %d." % (rc))
    _client.subscribe("#", qos=0)


def on_disconnect(_client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")
    server.stop()
    server.start()
    _client.reconnect()


def on_message(_client, _userdata, _msg):
    global devlist
    global devlock

    with devlock:
        if len(devlist) > 0:
            # distribute message to all devices
            for _dev in devlist:
                try:
                    _dev.mqttmessage(_msg)
                except:
                    pass


if __name__ == "__main__":
    print("Started...")
    # --------------------------------------------------------
    server = SSHTunnelForwarder(
        '94.16.117.246',
        ssh_username="franz",
        ssh_password="FK_s10rr6fr_246",
        remote_bind_address=('127.0.0.1', 1883)
    )

    # --------------------------------------------------------
    server.start()

    # print(server.local_bind_port)  # show assigned local port
    # work with `SECRET SERVICE` through `server.local_bind_port`.
    client = paho.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.username_pw_set("labor", "labor")
    client.connect("127.0.0.1", server.local_bind_port)

    thread_mqttloop = threading.Thread(target=mqttloop, args=(client,))
    thread_mqttloop.start()

    thread_detect_serial = threading.Thread(target=scan_serial_devices, args=(devices, comlist, comlock,))
    thread_detect_serial.start()

    thread_detect_ethernet = threading.Thread(target=scan_ethernet_devices, args=(devices, iplist, etherlock,))
    thread_detect_ethernet.start()
    '''
    # -------------------------------------------------------------------------------
    #                                   M Q T T
    # -------------------------------------------------------------------------------
    try:
        mqttclient = mqtt.Mqtt(ssh_host=config.ssh_tunnel["IP"],
                               ssh_user=config.ssh_tunnel["User"],
                               ssh_pass=config.ssh_tunnel["Password"],
                               mqtt_user=config.mqtt_broker["User"],
                               mqtt_pass=config.mqtt_broker["Password"])
    
        # wait for successful connection to mqtt-broker
        time_of_mqtt_connect_start = int(time.time() * 1000)
        while not mqttclient.connected:
            time.sleep(1)
            if int(time.time() * 1000) - time_of_mqtt_connect_start > 10000:
                raise Exception
        time.sleep(1)
    except:
        log("SSH tunnel could not be established or Mqtt-Broker not reachable.")
        app_exit()
    '''
    while True:
        # --------------------------------------------------------------------------
        # Die Comliste durchgehen und die entsprechende Deviceklasse erzeugen
        # --------------------------------------------------------------------------
        with comlock:
            if len(comlist) > 0:
                for com in comlist:
                    # print(com)
                    for d in deviceidentifications:
                        devobject = None
                        # print(d)
                        # print(devices[d]["classname"])
                        dclassname = devices[d]["classname"]
                        if dclassname in com:
                            # generating a deviceclass from classname
                            devobject = globals()[dclassname](com[dclassname])
                        if devobject is not None:
                            with devlock:
                                devlist.append(devobject)
                                devobject.on_created()

                comlist.clear()
        # --------------------------------------------------------------------------
        time.sleep(0.001)

        # --------------------------------------------------------------------------
        # Die bereits verbundenen Geräte durchgehen und execute aufrufen
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

    # server.stop()
