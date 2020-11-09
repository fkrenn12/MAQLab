import socket
import time

BUFFER_SIZE = 128  # max msg size
TIMEOUT_SECONDS = 10  # return error if we dont hear from supply within 10 sec


def scan_tcp_devices(devices, addresses, iplist, etherlock):
    idstrings = []
    iplist = []
    for d in devices:
        if d["interface"] == "ethernet":
            idstring = d["cmd_idn"]
            idstring = idstring.replace("<CR>", "\r")
            idstring = idstring.replace("<LF>", "\n")
            idstrings.append(idstring.encode("utf-8"))
    idstrings = list(set(idstrings))
    # TODO: bei TCP muss etwas anders vorgegangen werden!
    #
    '''
    p = platform.platform()
    if "Windows" in p:
        this_os = "Windows"
    else:
        this_os = "Linux"
    '''
    print("Start scanning...")
    print("->" + str(addresses))
    # -------------------------------------------------------------
    # LOOP
    # -------------------------------------------------------------
    while True:
        # print("Start check com")
        # time.sleep(1)
        # print("Scan ethernet ip...")
        for addr in addresses:
            try:
                print("->>" + str(addresses))
                print(str(addr))
                dev_found = None
                # -------------------------
                # opening socket connection
                # -------------------------
                supplySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # set up socket
                supplySocket.connect(addr)  # connect socket
                supplySocket.settimeout(TIMEOUT_SECONDS)
                buff = b''
                for ids in idstrings:
                    # the following sleep is necessary because a device
                    # which got a unknown command first needs time to recover
                    # internal for a new command. BK2831E needs 0.05sec,
                    # so at first we try four times more - 0.5sec
                    time.sleep(0.5)
                    try:
                        supplySocket.sendall(ids)
                        rep = supplySocket.recv(BUFFER_SIZE).decode("UTF-8").rstrip()
                    except:
                        continue

                    print(rep)
                    # ----------- end of reading loop --------------------
                    if rep != "":
                        for d in devices:
                            if d["idn_string"] in rep:
                                dev_found = d
                                break
                        if dev_found is not None:
                            break  # stop sending idstring because already found
                    # --------end of for loop writing idstrings ---------
                if buff == "":
                    continue  # next address

                # close serial port
                supplySocket.close()
                del supplySocket
                if dev_found is not None:
                    with etherlock:
                        iplist.append({dev_found["classname"]: addr})

            except:
                continue
        time.sleep(0.5)
