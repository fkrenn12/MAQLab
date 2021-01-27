from MAQLab import MQTT
from MAQLab import mqtt
import time
import xlwings as xw
import xlwings.utils as xwu
import threading
import os
import secrets

from datetime import datetime

debug = True
run_once = True

py_filename_without_extension = ""
py_filename = ""
xl_filename = ""

mqtt_hostname = "techfit.at"
mqtt_port = 1883
mqtt_user = "maqlab"
mqtt_pass = "maqlab"

stop_thread = False
error_cell_address = "A1"
status_measure_cell_address = "B1"
status_connection_cell_address = "E1"
active_devices = []

maqlab = None
accessnr = None
wertzahl = None
wertzahl = []


# --------------------------------------------------------------------------
def main():
    global py_filename_without_extension
    global py_filename
    global xl_filename
    global active_devices
    global maqlab

    if mqtt is not None:
        mqtt.close()

    py_filename = os.path.basename(__file__)
    # check .py extension
    py_filename_without_extension = py_filename.split(".")[0:-1][0]
    # find the excel file in the current dir
    # we are looking for xlsx and xlsm extension
    # as result we get the first occurrence of one of this
    # excel-files, so make sure that you will not have both
    # of them in the directory
    files = os.listdir(os.path.dirname(__file__))
    for f in files:
        fn = f.split(".")[0:-1][0]
        ex = f.split(".")[-1:][0]
        if fn == py_filename_without_extension:
            if ex == 'xlsx' or ex == 'xlsm':
                xl_filename = f
                break
    print("UDF-Server started")
    print("Filepath:", __file__)
    print("Python-Filename:", py_filename)
    print("Excel-Filename:", xl_filename)

    '''
    source.range('A1').expand().clear_contents()
    source.range('A1').value = cursor.fetchall()
    '''

    wb = xw.Book.caller()
    sht = wb.sheets.active

    sht.api.OLEObjects("Command1").Object.Visible = True
    sht.api.OLEObjects("MessageBox").Object.Visible = True
    sht.range(status_connection_cell_address).color = xwu.rgb_to_int((200, 200, 200))  # cell color
    sht.range(status_connection_cell_address).api.Font.Color = xwu.rgb_to_int((0, 0, 0))  # font color of text
    sht.range(status_connection_cell_address).value = "Connecting to: " + mqtt_hostname + ":" + str(mqtt_port)

    try:
        maqlab = MQTT(host=mqtt_hostname, port=mqtt_port, user=mqtt_user, password=mqtt_pass,
                      session_id=secrets.token_urlsafe(3).lower())
        sht.range(status_connection_cell_address).color = xwu.rgb_to_int((0, 200, 10))  # cell color
        sht.range(status_connection_cell_address).api.Font.Color = xwu.rgb_to_int((0, 0, 0))  # font color of text
        sht.range(status_connection_cell_address).value = "Connected"
    except:
        sht.range(status_connection_cell_address).color = xwu.rgb_to_int((200, 0, 10))  # cell color
        sht.range(status_connection_cell_address).api.Font.Color = xwu.rgb_to_int((255, 255, 255))  # font color of text
        sht.range(status_connection_cell_address).value = "Failed to connect"
        return

    active_devices = maqlab.available_devices()
    print(active_devices)

    # assembling text for messagebox
    text_messagebox = "Available Devices:\n"
    for device in active_devices:
        text_messagebox += "#" + str(device[1]) + "-" + device[0] + "\n"

    sht.api.OLEObjects("MessageBox").Object.Value = text_messagebox

    # reading the commands from the devices
    for device in active_devices:
        x1 = maqlab.send_and_receive_burst(maqlab.Msg(topic=str(device[1]) + "/?"))
        print(x1)

    # write available devices into combobox
    combo = 'ComboBox1'
    sht.api.OLEObjects(combo).Object.Clear()
    # sht.api.OLEObjects(combo).Object.ColumnCount = 2
    # sht.api.OLEObjects(combo).Object.ColumnWidths = 30
    for device in active_devices:
        sht.api.OLEObjects(combo).Object.AddItem("#" + str(device[1]) + "-" + device[0])


# --------------------------------------------------------------------------
def start(interval, count):
    if xl_filename == "":
        main()

    wb = xw.Book.caller()
    wb.sheets.active.range(error_cell_address).value = ""
    wb.sheets.active.api.OLEObjects("MessageBox").Object.Value = "Started...\n"

    # wb.sheets.active.api.OLEObjects("ComboBox").Object.Value = "some value"
    if isinstance(interval, str):
        try:
            interval = interval.replace(",", ".")  # Komma von , auf . ändern
            interval = float(interval)
        except:
            interval = 0
            wb.sheets.active.range(error_cell_address).value = "ERROR: Interval - invalid value format"
            return

    if isinstance(count, str):
        try:
            count = int(count)
            if count <= 0:
                wb.sheets.active.range(error_cell_address).value = "WARNING: Number of measure cycles is zero"
        except:
            wb.sheets.active.range(error_cell_address).value = "ERROR: Count - invalid value format"
            return

    # starting the measuring thread
    global stop_thread
    stop_thread = False
    x = threading.Thread(target=measure, args=(float(interval), int(count),))
    x.start()


# --------------------------------------------------------------------------
def stop():
    global stop_thread
    stop_thread = True


# --------------------------------------------------------------------------
def measure(t, count):
    global stop_thread
    global accessnr
    global wertzahl

    # accessing the sheet with index 0
    sht = xw.Book(xl_filename).sheets[0]  # sheet 0 = 1.Tabelle

    # Status zelle Text ändern und umfärben
    sht.range(status_measure_cell_address).api.Font.Color = xwu.rgb_to_int((0, 0, 0))  # font color of text
    sht.range(status_measure_cell_address).color = xwu.rgb_to_int((0, 200, 10))  # cell color
    sht.range(status_measure_cell_address).value = "Messung läuft"  # cell text
    print("Thread Running...")
    i = 0
    while i < count:
        print(i)
        sht.range("J5").value = str(i)
        sht.range("J6").value = str(count)

        # Index der Messung in Spalte A (=1)
        # das ist eine weitere Möglichkeit eine Zelle zu adressieren
        # ( Zeilennummer, Spaltennummer)
        cell = (i + 3, 1)
        sht.range(cell).value = str(i)

        # vorherige Zelle färben
        if i > 0:
            sht.range(i + 2, 1).color = xwu.rgb_to_int((100, 100, 100))

        # actuelle Zelle färben
        sht.range(cell).color = xwu.rgb_to_int((0, 200, 10))

        # -------------------------------------------

        global run_once
        if run_once:
            run_once = False
            Voltage = 0
            Current = 0
            Zeile = 3

        # sht.range('E32').value = [['TabKopfX', 'TabKopfY'], [1, 2], [10, 20]]

        # sht.range('C22').value = 'Verfuegbar'
        # sht.range('C23').value = active_devices

        accessnr = sht.range('N11').value
        accessnr = int(accessnr)

        # ----------------------------------------------------------------------

        sp1 = (sht["N14"].value)
        wert1 = str(accessnr) + "/" + str(sp1) + "?"
        print("Sending " + wert1)
        wertzahl = maqlab.send_and_receive(maqlab.Msg(topic=wert1)).payload
        print("Received " + wertzahl)
        # convert into real value
        # format is for instance  "0.543    VDC"
        wertzahl = float(wertzahl.split(" ")[0])

        cell = (i + 16, 14)
        sht.range(cell).value = wertzahl

        # ----------------------------------------------------------------------

        accessnr = sht.range('O11').value
        accessnr = int(accessnr)

        sp1 = (sht["O14"].value)
        wert1 = str(accessnr) + "/" + str(sp1) + "?"
        print("Sending " + wert1)
        wertzahl = maqlab.send_and_receive(maqlab.Msg(topic=wert1)).payload
        print("Received " + wertzahl)
        # convert into real value
        # format is for instance  "0.543    VDC"
        wertzahl = float(wertzahl.split(" ")[0])

        cell = (i + 16, 15)  # COL O is 15
        sht.range(cell).value = wertzahl

        # ------------------------------------------------------------------------
        # timing
        timer = 0
        while timer < t:
            if stop_thread:
                break
            time.sleep(0.01)
            timer = timer + 0.01
        if stop_thread:
            stop_thread = False
            break
        i += 1  # nächste Zeile

    # Statuszelle Text ändern und umfärben
    sht.range(status_measure_cell_address).api.Font.Color = xwu.rgb_to_int((255, 255, 255))
    sht.range(status_measure_cell_address).color = xwu.rgb_to_int((200, 10, 10))
    sht.range(status_measure_cell_address).value = "Messung gestopped"
    print("Thread Stopped")


if __name__ == '__main__':
    if debug:
        xw.serve()
    else:
        maqlab = MQTT(host=mqtt_hostname, port=mqtt_port, user=mqtt_user, password=mqtt_pass,
                      session_id=secrets.token_urlsafe(3).lower())
        try:
            active_devices = maqlab.available_devices()
            print(active_devices)
        except Exception as e:
            print(e)
        while True:
            time.sleep(1)
