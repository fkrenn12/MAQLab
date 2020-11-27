import socket
import time
import enum

EMPTY_BYTE_STRING = b''
EMPTY_STRING = ""
MINIMUM_TIME_IN_MS_BETWEEN_COMMANDS = 100  # not defined yet but we use 100 to test it
DEFAULT_PORT = 8462
BUFFER_SIZE = 1024  # max msg size
SM70AR24_VOLTAGE_HIGH_LIMIT = 70.0
SM70AR24_VOLTAGE_LOW_LIMIT = 0
SM70AR24_CURRENT_HIGH_LIMIT = 24.0
SM70AR24_CURRENT_LOW_LIMIT = 0


# --------------------------------------------------
class SM70AR24:
    # --------------------------------------------------
    # Class Constructor
    # --------------------------------------------------
    def __init__(self, addr):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # set up socket
        self.socket.settimeout(2)
        self.socket.connect(addr)  # connect socket

        self.__idstring = EMPTY_STRING
        self.__serialnumber = EMPTY_STRING
        self.__model = EMPTY_STRING
        self.__manufactorer = EMPTY_STRING
        self.__devicetype = EMPTY_STRING
        # self.__last_current = 0
        # self.__last_voltage = 0
        # self.__last_resistance = 0
        # self.__last_frequence = 0
        # self.__last_periode = 0
        # self.__last_current_unit = ""
        # self.__last_voltage_unit = ""
        # self.__last_resistance_unit = ""
        # self.__last_frequence_unit = ""
        # self.__last_periode_unit = ""
        self.__last_command_time = int(round(time.time() * 1000))

        # self.__mode = Mode.NONE
        self.id()
        # self.set_mode_vdc_auto_range()
        # --------------------------------------------------

    def connected(self):
        if self.socket is not None:
            rep = self.__send_and_receive_command("*idn?")
            if self.__serialnumber in rep:
                return True
        return False

    def __send_and_receive_command(self, command):
        command = command + "\n"
        try:
            self.socket.settimeout(0.5)
            self.socket.sendall(command.encode("UTF-8"))
            return self.socket.recv(BUFFER_SIZE).decode("UTF-8").rstrip()
        except:
            return ""

    # set value without receiving a response
    def __send_command(self, command):
        try:
            self.socket.settimeout(0.5)
            command = command + "\n"
            self.socket.sendall(command.encode("UTF-8"))
            return True
        except:
            return False

    # --------------------------------------------------
    def __wait_minimal_command_interval(self, ms_interval):
        while (int(round(time.time() * 1000)) - self.__last_command_time) < ms_interval:
            time.sleep(0.01)
        self.__last_command_time = int(round(time.time() * 1000))

    # --------------------------------------------------
    def id(self):
        try:
            # TODO -----> Check it
            self.__idstring = self.__send_and_receive_command("*idn?")
            if len(self.__idstring) > 0:
                t = self.__idstring.split(",")
                self.__model = t[1]
                self.__manufactorer = t[0]
                self.__serialnumber = t[2]
                self.__devicetype = "DC-Power Supply"
                # Initialise system

            else:
                raise
        except:
            self.__model = EMPTY_BYTE_STRING
            self.__manufactorer = EMPTY_BYTE_STRING
            self.__serialnumber = EMPTY_BYTE_STRING
            print("ERR - NO RESPONSE")

    # --------------------------------------------------

    def output_on(self):
        cmd = "OUTPUT 1"
        return bool(self.__send_command(cmd))

    # --------------------------------------------------

    def output_off(self):
        cmd = "OUTPUT 0"
        return bool(self.__send_command(cmd))

    # --------------------------------------------------
    def __del__(self):
        self.socket.close()

    # --------------------------------------------------
    def __get_serialnumber(self):
        return self.__serialnumber

    # --------------------------------------------------
    def __get_manufactorer(self):
        return self.__manufactorer

    # --------------------------------------------------
    def __get_devicetype(self):
        return self.__devicetype

    # --------------------------------------------------
    def __get_model(self):
        return self.__model

    # --------------------------------------------------
    serialnumber = property(__get_serialnumber)
    manufactorer = property(__get_manufactorer)
    devicetype = property(__get_devicetype)
    model = property(__get_model)


'''
import socket


# -- This module is not ready to work !!

class SM70AR24:
    def __init__(self, ip, port=8462):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # set up socket
        self.socket.connect((ip, port))  # connect socket
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
'''
