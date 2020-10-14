import serial
import time
import platform

scan_start = 2
scan_stop = 20
tout = 1000


def scan_serial_devices(devices, comlist, comlock):
    deviceidentifications = list(devices.keys())
    idstrings = []
    for d in devices:
        if devices[d]["interface"] == "usb-vcom":
            idstrings.append(devices[d]["cmd_idn"].encode("utf-8"))
        # idstrings.append(devices[d]["cmd_idn"])
    # idstrings.sort()
    idstrings = list(set(idstrings))
    # idstrings.sort()

    p = platform.platform()
    if "Windows" in p:
        this_os = "Windows"
    else:
        this_os = "Linux"
    # -------------------------------------------------------------
    # LOOP
    # -------------------------------------------------------------
    while True:
        # print("Start check com")
        for number in range(scan_start, scan_stop):
            try:
                # this is for windows
                _com = "com" + str(number)
                # print("NEW COM TESTING: " + _com)
                ser = serial.Serial(_com, baudrate=9600)
                ser.timeout = 1
                buff = b''
                for ids in idstrings:
                    # the following sleep is necessary because a device
                    # which got a unknown command first needs time to recover
                    # internal for a new command. BK2831E needs 0.05sec,
                    # so at first we try four times more - 0.5sec
                    time.sleep(0.5)
                    try:
                        ser.flush()
                        ser.flushInput()
                        # print("SEND")
                        # print(ids)
                        ser.write(ids)
                    except:
                        continue

                    # ---------  reading loop  ---------------------------
                    tic = int(round(time.time() * 1000))
                    buff = b''
                    while (int(round(time.time() * 1000)) - tic) < tout:
                        time.sleep(0.005)
                        if ser.in_waiting > 0:
                            tic = int(round(time.time() * 1000))
                            c = ser.read(1)
                            if c != b'\n' and c != b'\r':
                                buff += c
                    # ----------- end of reading loop --------------------
                    if buff != b'':
                        found = False
                        for _d in deviceidentifications:
                            # print(devices[d]["idn_string"].encode())
                            if devices[_d]["idn_string"].encode() in buff:
                                found = True
                                break
                        if found:
                            break  # stop sending idstring because already found
                    # --------end of for loop writing idstrings ---------
                if buff == b'':
                    continue  # next com port

                # close serial port
                ser.close()
                del ser
                # search for device and add it to comlist
                for _d in deviceidentifications:
                    # print(devices[d]["idn_string"].encode())
                    if devices[_d]["idn_string"].encode() in buff:
                        # search for inventarnumber of this device
                        with comlock:
                            comlist.append({devices[_d]["classname"]: _com})
                            # print("Found " + devices[d]["classname"])
                            break
            except:
                continue
        time.sleep(0.5)