import time
import xlwings as xw
from xlwings import constants
import xlwings.utils as xwu
import paho.mqtt.client as paho
import threading
import json
import os
import secrets
from pydispatch import dispatcher
import jsontable as jsontable

FILENAME_CONFIG_DEVICES = "devices.json"
FILENAME_CONFIG_INVENTAR = "inventar.json"
MQTT = "mqtt"
MQTT_RECEIVE_INVENTAR = "inventar"
MQTT_RECEIVE_DEVICES = "devices"
py_filename_without_extension = ""
py_filename = ""
xl_filename = ""
row_start = 5
col_start = 2
COLOR_PROVIDER_TABLE_HEADER = 0x80C0ff
COLOR_PROVIDER_TABLE_LINE_ALTER = 0xE3EEFF

global wb
global xb
global client
global lock
global config_string
global session_id


def print_json_into_excel_sheet(sht, _row_start, _col_start, path, jsons):
    col = _col_start
    row = _row_start

    # Create an instance of a converter
    convert_inventar = jsontable.converter()
    # Set the paths you want to extract
    convert_inventar.set_paths(path)
    # Input a JSON to be interpreted
    table = convert_inventar.convert_json(jsons)
    # convert all None into "---"
    for i in range(0, len(table)):
        subtable = table[i]
        for j in range(0, len(subtable)):
            value = subtable[j]
            if value is None or value == "none":
                value = "*"
            subtable[j] = value
    # print(table)
    # header
    sht.range(row, col).value = table[0]
    sht.range(row, col).expand("right").api.HorizontalAlignment = constants.HAlign.xlHAlignCenter
    sht.range(row, col).expand("right").color = COLOR_PROVIDER_TABLE_HEADER
    # table with data
    sht.range(row + 2, col).value = table[1:]
    sht.range("A1:Z100").autofit()
    sht.range(row + 2, col).expand("table").api.HorizontalAlignment = constants.HAlign.xlHAlignRight


# --------------------------------------------------------
# MQTT Broker handler functions
# --------------------------------------------------------
def mqttloop(_client):
    client.loop_forever()


def on_connect(_client, userdata, flags, rc):
    if rc == 0:
        # print("CONNACK received with code %d." % (rc))
        print("Connected :-) ")
        _client.subscribe("maqlab/" + session_id + "/rep/file/#", qos=0)


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
    completed = True
    topic_received = msg.topic.lower()
    config_string = msg.payload.decode("utf-8")
    if FILENAME_CONFIG_DEVICES in topic_received:
        dispatcher.send(message=msg.payload.decode("utf-8"),
                        signal=MQTT_RECEIVE_DEVICES,
                        sender=MQTT)
    if FILENAME_CONFIG_INVENTAR in topic_received:
        dispatcher.send(message=msg.payload.decode("utf-8"),
                        signal=MQTT_RECEIVE_INVENTAR,
                        sender=MQTT)
    # print(config_string)


# --------------------------------------------------------
#               DISPATCHER  handler functions
# --------------------------------------------------------
def on_mqtt_receive_inventar(message):
    book = xw.Book(xl_filename)
    try:
        book.sheets["Inventar"]
    except:
        book.sheets.add("Inventar", after="Geräte")
    sht = book.sheets["Inventar"]
    sht.clear()
    # Create a list of paths you want to extract
    path = [{"$.inventar_number": "Inventarnummer"},
            {"$.device": "Gerät"},
            {"$.serial": "Seriennummer"},
            {"$.ipaddress": "IP-Adresse"},
            {"$.port": "Port"}]

    print_json_into_excel_sheet(sht=sht,
                                _row_start=row_start,
                                _col_start=col_start,
                                path=path,
                                jsons=json.loads(message))


def on_mqtt_receive_devices(message):
    book = xw.Book(xl_filename)
    try:
        book.sheets["Geräte"]
    except:
        book.sheets.add("Geräte")
    sht = book.sheets["Geräte"]
    sht.clear()
    # Create a list of paths you want to extract
    path = [{"$.device": "Bezeichnung"},
            {"$.devicetype": "Typ"},
            {"$.manufactorer": "Hersteller"},
            {"$.cmd_idn": "SCPI Identify Befehl"},
            {"$.cmd_term": "SCPI Endzeichen"},
            {"$.classname": "Klassenname"},
            {"$.interface": "Interface"},
            {"$.baudrate": "Baudrate"}
            ]
    print_json_into_excel_sheet(sht=sht,
                                _row_start=row_start,
                                _col_start=col_start,
                                path=path,
                                jsons=json.loads(message))


# --------------------------------------------------------------------------
#                                   M A I N
# --------------------------------------------------------------------------
def main():
    global py_filename_without_extension
    global py_filename
    global xl_filename
    global lock
    global session_id
    # global xb

    dispatcher.connect(on_mqtt_receive_inventar, signal=MQTT_RECEIVE_INVENTAR,
                       sender=MQTT)
    dispatcher.connect(on_mqtt_receive_devices, signal=MQTT_RECEIVE_DEVICES,
                       sender=MQTT)

    lock = threading.Lock()
    session_id = secrets.token_urlsafe(5)
    # xb = xw.Book(xl_filename)

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
    # initialize()


# --------------------------------------------------------------------------
#                       I N I T I A L I Z E - Button
# --------------------------------------------------------------------------
def initialize():
    global wb
    print("Request configuration")
    client.publish("maqlab/" + session_id + "/cmd/file/get", "/config/" + FILENAME_CONFIG_INVENTAR)
    client.publish("maqlab/" + session_id + "/cmd/file/get", "/config/" + FILENAME_CONFIG_DEVICES)


# --------------------------------------------------------------------------
#                            U P L O A D - Button
# --------------------------------------------------------------------------
def upload():
    global wb
    print("Sorry, Upload not yet implemented")

# --------------------------------------------------------------------------
main()
