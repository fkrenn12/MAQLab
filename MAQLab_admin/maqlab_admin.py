import time
import global_share
import xlwings as xw
import xlwings.utils as xwu
import paho.mqtt.client as paho
import threading
import json
import os

py_filename_without_extension = ""
py_filename = ""
xl_filename = ""
global wb
global client
global lock
global config_string
global completed


# --------------------------------------------------------
# MQTT Broker callbacks
# --------------------------------------------------------
def mqttloop(_client):
    client.loop_forever()


def on_connect(_client, userdata, flags, rc):
    # print("CONNACK received with code %d." % (rc))
    print("Connected :-) ")
    _client.subscribe("maqlab/file/#", qos=0)


def on_disconnect(_client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")
    # server.stop()
    # server.start()
    _client.reconnect()


def on_message(_client, userdata, msg):
    global lock
    global config_string
    global completed
    print(msg.topic, msg.payload)
    topic_received = msg.topic.lower()
    topic_received_split = topic_received.split("/")
    state = topic_received_split[3]
    if state == "start":
        with lock:
            print("Startet transmitting ...")
            config_string = ""
            completed = False
    elif state == "finish":
        with lock:
            completed = True
            print("Finished transmitting...")
    elif state.isnumeric():
        state = int(state)
        with lock:
            print("Received data...#" + str(state))
            config_string = config_string + msg.payload.decode("utf-8")
        pass


# --------------------------------------------------------------------------
def main():
    global py_filename_without_extension
    global py_filename
    global xl_filename
    global lock

    lock = threading.Lock()

    # sht = None

    py_filename = os.path.basename(__file__)
    # print(py_filename)
    # check .py extension
    py_filename_without_extension = py_filename.split(".")[0:-1][0]
    # print(py_filename_without_extension)
    # find the excel file in the current dir
    # we are looking for xlsx and xlsm extension
    # as result we get the first occurrence of one of this
    # excel-files, so make sure that you will not have both
    # of them in the directory
    files = os.listdir(os.path.dirname(__file__))
    for f in files:
        # print(f)
        try:
            fn = f.split(".")[0:-1][0]
            ex = f.split(".")[-1:][0]
            if fn == py_filename_without_extension:
                if ex == 'xlsx' or ex == 'xlsm':
                    xl_filename = f
                    break
        except:
            pass
    print("UDF-Server started")
    print("Filepath:", __file__)
    print("Python-Filename:", py_filename)
    print("Excel-Filename:", xl_filename)
    print("Connecting to MQTT-Broker...")
    global client
    client = paho.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.username_pw_set("maqlab", "maqlab")
    client.connect("techfit.at", 1883)

    thread_mqttloop = threading.Thread(target=mqttloop, args=(client,))
    thread_mqttloop.start()
    time.sleep(1)
    # source.range('A1').expand().clear_contents()
    # source.range('A1').value = cursor.fetchall()

    global wb
    wb = xw.Book.caller()


# --------------------------------------------------------------------------
def initialize():
    global wb
    global completed
    print("Request configuration")
    completed = False
    client.publish("maqlab/file/?", "/config/devices.json")
    while True:
        with lock:
            if completed:
                break
        time.sleep(0.1)
    # Receive completed
    print(config_string)
    # write it to excel


# --------------------------------------------------------------------------
def upload():
    global wb


# --------------------------------------------------------------------------
main()
