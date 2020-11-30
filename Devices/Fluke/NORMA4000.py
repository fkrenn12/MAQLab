import socket
import time
import enum

EMPTY_BYTE_STRING = b''
EMPTY_STRING = ""
MINIMUM_TIME_IN_MS_BETWEEN_COMMANDS = 100  # not defined yet but we use 100 to test it
DEFAULT_PORT = 23
BUFFER_SIZE = 1024  # max msg size


# --------------------------------------------------
class NORMA4000:
    # --------------------------------------------------
    # Class Constructor
    # --------------------------------------------------
    def __init__(self, addr):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # set up socket
        self.socket.settimeout(10)
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
            self.socket.settimeout(5)
            self.socket.sendall(command.encode("UTF-8"))
            return self.socket.recv(BUFFER_SIZE).decode("UTF-8").rstrip()
        except:
            return ""

    # set value without receiving a response
    def __send_command(self, command):
        try:
            self.socket.settimeout(5)
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
            self.__idstring = self.__send_and_receive_command("*idn?")
            if len(self.__idstring) > 0:
                t = self.__idstring.split(",")
                self.__model = t[1]
                self.__manufactorer = t[0]
                self.__serialnumber = t[2]
                self.__devicetype = "Power Analyser"
                # Initialise system
                # TODO
            else:
                raise
        except:
            self.__model = EMPTY_BYTE_STRING
            self.__manufactorer = EMPTY_BYTE_STRING
            self.__serialnumber = EMPTY_BYTE_STRING
            print("ERR - NO RESPONSE")

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
