import serial
import time
import platform

scan_start = 2
scan_stop = 40
tout = 1000


def scan_serial_devices(devices, comlist, comlock):
    deviceidentifications = list(devices.keys())
    idstrings = []
    for d in devices:
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
                # print(idstrings)
                buff = b''
                for ids in idstrings:
                    # the following sleep is necessary because a device
                    # which got a unknown command first needs time to recover
                    # internal for a new command. BK2831E needs 0.05sec,
                    # so at first we try four times more - 0.2sec
                    time.sleep(0.2)
                    try:
                        # print("FLUSH")
                        ser.flush()
                        ser.flushInput()
                    except:
                        # print("FLUSH - ERROR")
                        continue
                    # print(len(ids))
                    # termchar = ids[len(ids) - 1].encode("utf-8")
                    termchar = b""
                    if ids[len(ids) - 1] == 10:
                        termchar = b"\n"
                    if ids[len(ids) - 1] == 13:
                        termchar = b"\r"

                    # print(termchar)
                    # print("+1")
                    try:
                        # print("SEND")
                        # print(ids)
                        ser.write(ids)
                    except:
                        pass
                        # print("LOOP1 - WRITE ERROR")
                    # ser.write(b'*idn?\n')
                    # print(ids)
                    # ser.write(b'GMOD\r')
                    # print("+2")

                    tic = int(round(time.time() * 1000))
                    buff = b''
                    while (int(round(time.time() * 1000)) - tic) < tout:
                        if ser.in_waiting > 0:
                            # print("LOOP1 - DATA Waiting")
                            # print("#"+str(ser.in_waiting))
                            c = ser.read(1)
                            # print(c)
                            # print(termchar)
                            if c != termchar:
                                buff += c
                                # print(buff)
                            else:
                                # print("LOOP1 - BREAK")
                                break
                        #time.sleep(0.01)
                    if int(round(time.time() * 1000)) - tic >= tout:
                        # ser.close()
                        # del ser
                        # print("LOOP1 - TIMEOUT")
                        continue
                    # print("RETURN")
                    # print(buff)
                    ids = ids.rstrip()
                    # print("LOOP1 - FINISHED")
                    # print("BUFF:" + str(buff) + "IDS: " + str(ids))
                    if buff == ids:
                        # print("LOOP2 - ENTERED")
                        # the device repeated the command
                        # so we get the id from the second reply
                        # pass
                        # print("+3")

                        tic = int(round(time.time() * 1000))
                        buff = b''
                        while (int(round(time.time() * 1000)) - tic) < tout:
                            if ser.in_waiting > 0:
                                # print("LOOP2 - DATA Waiting")
                                c = ser.read(1)
                                # print(c)
                                if c != termchar:
                                    buff += c
                                    # print("LOOP2 - TERMCHAR")
                                else:
                                    # print("LOOP2 - BREAK")
                                    break
                            time.sleep(0.01)
                        if int(round(time.time() * 1000)) - tic >= tout:
                            # ser.close()
                            # del ser
                            # print("LOOP2 - TIMEOUT")
                            continue
                        break
                    else:
                        break

                idstring = buff
                ser.close()
                del ser
                # print(idstring)
                # ser.readline()
                # print("+4")
                for _d in deviceidentifications:
                    # print(devices[d]["idn_string"].encode())
                    if devices[_d]["idn_string"].encode() in idstring:
                        with comlock:
                            comlist.append({devices[_d]["classname"]: _com})
                            # print("Found " + devices[d]["classname"])
                            break
            except:
                # print("COM - ERROR\n")
                # time.sleep(1)
                continue
        time.sleep(0.5)
