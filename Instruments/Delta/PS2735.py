import socket

# -- This module is not ready to work !!

class Delta:
    def __init__(self, ip, port=8462):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # set up socket
        self.socket.connect(ip, port)  # connect socket
        self.socket.settimeout(10)

    def sendAndReceiveCommand(self, msg):
        msg = msg + "\n"
        self.socket.sendall(msg.encode("UTF-8"))
        return self.socket.recv(BUFFER_SIZE).decode("UTF-8").rstrip()

    # set value without receiving a response
    def sendCommand(self, msg):
        msg = msg + "\n"
        self.socket.sendall(msg.encode("UTF-8"))

    def setOutputState(self, state):
        if state:
            self.sendCommand("OUTPUT 1")
        else:
            self.sendCommand("OUTPUT 0")

    def __del__(self):
        self.socket.close()


def setRemoteShutdownState(state):
    if state:
        sendCommand("SYST:RSD 1")
    else:
        sendCommand("SYST:RSD 0")


def setVoltage(volt):
    retval = 0
    if volt >= 0 and volt <= MAX_VOLT:
        sendCommand("SOUR:VOLT {0}".format(volt))
    else:

        retval = -1

    return retval


def setCurrent(cur):
    retval = 0
    if cur >= 0 and cur <= MAX_VOLT:
        sendCommand("SOUR:CURR {0}".format(cur))
    else:
        retval = -1

    return retval


def readVoltage():
    return sendAndReceiveCommand("SOUR:VOLT?")


def readCurrent():
    return sendAndReceiveCommand("SOUR:CURR?")


def closeSocket():
    supplySocket.close()


# -----------------------------------------------------------------

if __name__ == "__main__":
    try:
        SUPPLY_IP = "172.16.65.115"
        SUPPLY_PORT = 8462
        BUFFER_SIZE = 128  # max msg size
        TIMEOUT_SECONDS = 10  # return error if we dont hear from supply within 10 sec
        MAX_VOLT = 70  # default
        MAX_CUR = 24  # default

        supplySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # set up socket
        supplySocket.connect((SUPPLY_IP, SUPPLY_PORT))  # connect socket
        supplySocket.settimeout(TIMEOUT_SECONDS)

        print(sendAndReceiveCommand("*IDN?"))
        MAX_VOLT = float(sendAndReceiveCommand("SOUR:VOLT:MAX?"))
        MAX_CUR = float(sendAndReceiveCommand("SOUR:CURR:MAX?"))

        print(MAX_VOLT, MAX_CUR)
        # Voltage control: "REM" remote , "LOC" local from panel
        sendCommand("SYST:REM:CV REM");
        # Current control: "REM" remote , "LOC" local from panel
        sendCommand("SYST:REM:CC REM");
        # "Output 1" = ON , "Output 0" = OFF
        sendCommand("OUTPUT 1")
        setRemoteShutdownState(0)  # 0 supply on , 1 supply off/disabled

        setVoltage(19.23)
        setCurrent(0.8)

        print(readVoltage())  # setted value but not real value
        print(readCurrent())  # setted value but not real value

    finally:
        closeSocket()
# -----------------------------------------------------------------
