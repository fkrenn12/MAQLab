import os
import secrets
import sys
import threading
import time
import datetime
import re

import xlwings as xw
import xlwings.utils as xwu

# Adding the ../MAQLab/.. folder to the system path of python
# It is temporarily used only by this script
script_dir = str()
try:
    script_dir = os.path.dirname(__file__)
    maqlab_dir = "\\maqlab"
    script_dir = script_dir[0:script_dir.index(maqlab_dir)] + maqlab_dir
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
except:
    pass

from MAQLab import MqttMsg
from MAQLab import maqlab

run_once = True

py_filename_without_extension = ""
py_filename = ""
xl_filename = ""

stop_thread = False
error_cell_address = "A1"
status_measure_cell_address = "B1"
status_connection_cell_address = "E1"
active_devices = list()
active_devices_commands = list()
active_devices_manufactorers = list()
active_devices_models = list()
active_devices_types = list()

sht_maqlab_config = None
accessnr = None
wertzahl = None


# --------------------------------------------------------------------------
# main() - will be invoked by pressing initialize
# --------------------------------------------------------------------------
def main():
    global py_filename_without_extension
    global py_filename
    global xl_filename
    global active_devices
    global sht_maqlab_config

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
    # print("UDF-Server started")
    # print("Filepath:", __file__)
    # print("Python-Filename:", py_filename)
    # print("Excel-Filename:", xl_filename)

    '''
    source.range('A1').expand().clear_contents()
    source.range('A1').value = cursor.fetchall()
    '''

    wb = xw.Book.caller()


    try:
        wb.sheets.add("maqlab.conf", "xlwings.conf")
    except:
        pass

    try:
        sht_maqlab_config = wb.sheets["maqlab.conf"]
    except:
        sht_maqlab_config = None

    sht = wb.sheets["Automatic"]
    sht.api.OLEObjects("Command1").Object.Visible = True  # nur test
    sht.api.OLEObjects("MessageBox").Object.Visible = True  # nur test
    sht.range(status_connection_cell_address).color = xwu.rgb_to_int((200, 200, 200))  # cell color
    sht.range(status_connection_cell_address).api.Font.Color = xwu.rgb_to_int((0, 0, 0))  # font color of text
    if maqlab is not None and maqlab.is_connected:
        sht.range(status_connection_cell_address).color = xwu.rgb_to_int((0, 200, 10))  # cell color
        sht.range(status_connection_cell_address).api.Font.Color = xwu.rgb_to_int((0, 0, 0))  # font color of text
        sht.range(status_connection_cell_address).value = "Connected"
    else:
        sht.range(status_connection_cell_address).color = xwu.rgb_to_int((200, 0, 10))  # cell color
        sht.range(status_connection_cell_address).api.Font.Color = xwu.rgb_to_int((255, 255, 255))  # font color of text
        sht.range(status_connection_cell_address).value = "MAQlab not Connected"
        return
    reload()


# --------------------------------------------------------------------------
# reload() - will be invoked by pressing the "Reload Devices" button
# --------------------------------------------------------------------------
def reload():
    wb = xw.Book.caller()
    sht = wb.sheets["Automatic"]
    maqlab.load_devices()
    # creating text for messagebox

    # TODO hier noch löschen der Zellen bevor aktualisiert wird
    sht_maqlab_config.range((1, 1)).value = ["Accessnumber", "Model", "Manufactorer", "Type"]

    text_messagebox = "Available Devices:\n"
    text_messagebox += "#\tModell\t\tType\n"
    index = 0
    row = 2
    for model in maqlab.device_models:
        row += 1
        sht_maqlab_config.range((row, 1)).value = [str(maqlab.device_accessnumbers[index]),
                                                   model,
                                                   str(maqlab.device_manufactorers[index]),
                                                   maqlab.device_types[index],
                                                   maqlab.device_commands[index]]

        text_messagebox += "#" + str(maqlab.device_accessnumbers[index]) + "\t" + model \
                           + "\t" + maqlab.device_manufactorers[index] \
                           + "\t" + maqlab.device_types[index] + "\n"
        index += 1
    # send it to excel
    sht.api.OLEObjects("MessageBox").Object.Value = text_messagebox

    # print("Active devices detected: ", maqlab.device_models)
    # print("Active devices manufactorer ", maqlab.device_manufactorers)
    # print("Active devices accessnumber ", maqlab.device_accessnumbers)
    # print("Active devices type ", maqlab.device_types)
    # print("Active devices commands: ", maqlab.device_commands)

    # write available devices into combobox
    combo = 'ComboBox1'
    sht.api.OLEObjects(combo).Object.Clear()
    # sht.api.OLEObjects(combo).Object.ColumnCount = 2
    # sht.api.OLEObjects(combo).Object.ColumnWidths = 30
    # for device in active_devices:
    # sht.api.OLEObjects(combo).Object.AddItem("#" + str(device[1]) + "-" + device[0])


# --------------------------------------------------------------------------
# start() - will be invoked by pressing the "Start" button
# --------------------------------------------------------------------------
def start(interval, count):
    if xl_filename == "":
        main()

    wb = xw.Book.caller()
    wb.sheets.active.range(error_cell_address).value = ""

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
# stop() - will be invoked by pressing the "Stop" button
# --------------------------------------------------------------------------
def stop():
    global stop_thread
    stop_thread = True


# --------------------------------------------------------------------------
# thread function measure
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

        command = str(sht["N14"].value)
        print("Sending " + command + " to " + str(accessnr))
        wertzahl = maqlab.send_and_receive(accessnumber=accessnr, command=command).payload
        print("Received " + wertzahl)
        # convert into real value from string with unit
        # format is for instance  "0.543 VDC"
        wertzahl = re.sub("[A-Za-z ]", "", wertzahl)

        cell = (i + 16, 14)
        sht.range(cell).value = wertzahl

        # ----------------------------------------------------------------------

        accessnr = sht.range('O11').value
        accessnr = int(accessnr)

        command = str(sht["O14"].value)
        print("Sending " + command + " to " + str(accessnr))
        wertzahl = maqlab.send_and_receive(accessnumber=accessnr, command=command).payload
        print("Received " + wertzahl)
        # convert into real value from string with unit
        # format is for instance  "0.543    VDC"
        wertzahl = re.sub("[A-Za-z ]", "", wertzahl)

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
    sht.range(status_measure_cell_address).value = "Messung fertig"
    print("Thread Stopped")


if __name__ == '__main__':
    xw.serve()
