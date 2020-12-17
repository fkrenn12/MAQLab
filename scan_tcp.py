import socket
import time
import asyncio
import datetime

BUFFER_SIZE = 128  # max msg size
CONNECT_TIMEOUT_SECONDS = 0.5


async def scan_tcp_devices(devices, addresses, iplist):
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
    print(str(datetime.datetime.now()) + "  :" + "Start TCP scanning...")
    # print("->" + str(addresses))
    # -------------------------------------------------------------
    # LOOP
    # -------------------------------------------------------------
    while True:
        # print("Scan network...")
        # print("Scan ->>" + str(addresses))
        for addr in addresses:
            try:
                # print("->> " + str(addr))
                dev_found = None
                # -------------------------------------
                # close and  delete socket if existing
                # -------------------------------------
                try:
                    scan_socket
                    try:
                        scan_socket.close()
                    except:
                        pass
                    del scan_socket
                except:
                    pass
                # -------------------------
                # opening socket connection
                # -------------------------
                scan_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # set up socket
                scan_socket.setblocking(True)
                scan_socket.settimeout(0.1)
                timeout_counter = 0
                while True:
                    try:
                        scan_socket.connect(addr)  # connect socket
                        break
                    except:
                        await asyncio.sleep(0.2)
                        # print(str(datetime.datetime.now()) + ":")
                        timeout_counter += 1
                    if timeout_counter > 5:
                        raise

                # print(str(datetime.datetime.now()) + "Socket: Connected")

                for ids in idstrings:
                    # the following sleep is necessary because a device
                    # which got a unknown command first needs time to recover
                    # internal for a new command. BK2831E needs 0.05sec,
                    # so at first we try four times more - 0.5sec
                    # time.sleep(0.5)
                    await asyncio.sleep(0.5)
                    # ------------------------------
                    # sending the identifier command
                    # ------------------------------
                    timeout_counter = 0
                    while True:
                        try:
                            scan_socket.sendall(ids)
                            break
                        except:
                            await asyncio.sleep(0.1)
                            timeout_counter += 1
                        if timeout_counter > 10:
                            raise
                    # -----------------------------------
                    # reply from the identifier command
                    # -----------------------------------
                    timeout_counter = 0
                    while True:
                        try:
                            rep = scan_socket.recv(BUFFER_SIZE).decode("UTF-8").rstrip()
                            break
                        except:
                            await asyncio.sleep(0.1)
                            timeout_counter += 1
                        if timeout_counter > 10:
                            raise
                    # print(rep)
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

                scan_socket.setblocking(True)
                scan_socket.settimeout(0.5)
                if dev_found is not None:
                    # close connection
                    try:
                        scan_socket.close()
                        del scan_socket
                        # print("Socket: Delete")
                    except:
                        pass
                    # print("Socket: Close")
                    # with etherlock:
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
        await asyncio.sleep(0.5)

