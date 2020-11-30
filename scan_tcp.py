import socket
import time

BUFFER_SIZE = 128  # max msg size
CONNECT_TIMEOUT_SECONDS = 0.5


def scan_tcp_devices(devices, addresses, iplist, etherlock):
    idstrings = []
    # iplist = []
    for d in devices:
        if d["interface"] == "ethernet":
            idstring = d["cmd_idn"]
            idstring = idstring.replace("<CR>", "\r")
            idstring = idstring.replace("<LF>", "\n")
            idstrings.append(idstring.encode("utf-8"))
    idstrings = list(set(idstrings))

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
        # print("Scan network...")
        # print("Scan ->>" + str(addresses))
        for addr in addresses:
            try:
                print("->> " + str(addr))
                dev_found = None
                # -------------------------
                # opening socket connection
                # -------------------------
                scan_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # set up socket
                # print("Socket: New Socket")
                scan_socket.settimeout(CONNECT_TIMEOUT_SECONDS)
                # print("Socket: Set Timeout")
                scan_socket.connect(addr)  # connect socket
                # print("Socket: Connected")

                for ids in idstrings:
                    # the following sleep is necessary because a device
                    # which got a unknown command first needs time to recover
                    # internal for a new command. BK2831E needs 0.05sec,
                    # so at first we try four times more - 0.5sec
                    time.sleep(0.5)
                    try:
                        scan_socket.sendall(ids)
                        rep = scan_socket.recv(BUFFER_SIZE).decode("UTF-8").rstrip()
                    except:
                        continue

                    print(rep)
                    # ----------- end of reading loop --------------------
                    if rep != "":
                        for d in devices:
                            if d["idn_string"] in rep:
                                dev_found = d
                                # print("Found: " + d["idn_string"])
                                break
                        if dev_found is not None:
                            break  # stop sending idstring because already found
                    # --------end of for loop writing idstrings ---------

                if dev_found is not None:
                    # close connection
                    try:
                        scan_socket.close()
                        del scan_socket
                        # print("Socket: Delete")
                    except:
                        pass
                    # print("Socket: Close")
                    with etherlock:
                        if iplist.count({dev_found["classname"]: addr}) == 0:
                            iplist.append({dev_found["classname"]: addr})
            except:
                pass
            finally:
                # close connection
                try:
                    scan_socket.close()
                    del scan_socket
                    # print("Socket: Delete")
                except:pass
                # print("Socket: Close")


        time.sleep(10)
