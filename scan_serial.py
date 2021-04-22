import serial
import time
import datetime
import platform
import asyncio

scan_start = 4
scan_stop = 12
tout = 1000


async def scan_serial_devices(devices, comlist):
    # TODO  idstrings can be managed different better
    idstrings = []
    for d in devices:
        if d["interface"] == "usb-vcom":
            idstring = d["cmd_idn"]
            idstring = idstring.replace("<CR>", "\r")
            idstring = idstring.replace("<LF>", "\n")
            idstrings.append(idstring.encode("utf-8"))
    idstrings = list(set(idstrings))

    p = platform.platform()
    if "Windows" in p:
        this_os = "Windows"
    else:
        this_os = "Linux"

    print(str(datetime.datetime.now()) + "  :" + "Start scanning SERIAL Ports... ")
    # -------------------------------------------------------------
    # LOOP
    # -------------------------------------------------------------
    while True:
        # print("Start check com")
        for number in range(scan_start, scan_stop + 1):
            try:
                dev_found = None
                # this is for windows
                _com = "com" + str(number)
                ser = serial.Serial(_com, baudrate=9600, timeout=1)
                ser.timeout = 1
                buff = b''
                for ids in idstrings:
                    # the following sleep is necessary because a device
                    # which got a unknown command first needs time to recover
                    # internal for a new command. BK2831E needs 0.05sec,
                    # so at first we try four times more - 0.5sec
                    await asyncio.sleep(0.5)
                    try:
                        ser.flush()
                        ser.flushInput()
                        ser.write(ids)
                    except:
                        continue

                    # ---------  reading loop  ---------------------------
                    tic = int(round(time.time() * 1000))
                    buff = b''
                    while (int(round(time.time() * 1000)) - tic) < tout:
                        await asyncio.sleep(0.005)
                        if ser.in_waiting > 0:
                            tic = int(round(time.time() * 1000))
                            c = ser.read(1)
                            if c != b'\n' and c != b'\r':
                                buff += c
                    # ----------- end of reading loop --------------------
                    if buff != b'':
                        # print(buff)
                        for d in devices:
                            if d["idn_string"] in buff.decode("utf-8"):
                                dev_found = d
                                break
                        if dev_found is not None:
                            break  # stop sending idstring because already found
                    # --------end of for loop writing idstrings ---------
                if buff == b'':
                    continue  # next com port

                # close serial port
                ser.close()
                del ser
                if dev_found is not None:
                    comlist.append({dev_found["classname"]: _com})

            except:
                continue
        await asyncio.sleep(0.5)
