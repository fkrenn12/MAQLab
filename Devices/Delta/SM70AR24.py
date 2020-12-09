import socket
import time
import enum

SOCKET_TIMEOUT_SECONDS = 1
EMPTY_BYTE_STRING = b''
EMPTY_STRING = ""
MINIMUM_TIME_IN_MS_BETWEEN_COMMANDS = 100  # not defined yet but we use 100 to test it
DEFAULT_PORT = 8462
BUFFER_SIZE = 1024  # max msg size
SM70AR24_VOLTAGE_HIGH_LIMIT = 70.0
SM70AR24_VOLTAGE_LOW_LIMIT = 0
SM70AR24_CURRENT_HIGH_LIMIT = 24.0
SM70AR24_CURRENT_LOW_LIMIT = 0

HUMAN_SECURE_MAX_VOLTAGE = 50
VOLT_UNDEFINED_VALUE = -999999.99
CURRENT_UNDEFINED_VALUE = -999999.99

# --------------------------------------------------
class SM70AR24:
    # --------------------------------------------------
    # Class Constructor
    # --------------------------------------------------
    def __init__(self,
                 addr,
                 voltage_low_limit=SM70AR24_VOLTAGE_LOW_LIMIT,
                 voltage_high_limit=SM70AR24_VOLTAGE_HIGH_LIMIT,
                 current_low_limit=SM70AR24_CURRENT_LOW_LIMIT,
                 current_high_limit=SM70AR24_CURRENT_HIGH_LIMIT):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # set up socket
        self.socket.settimeout(2)
        self.socket.connect(addr)  # connect socket

        self.__idstring = EMPTY_STRING
        self.__serialnumber = EMPTY_STRING
        self.__model = EMPTY_STRING
        self.__manufactorer = EMPTY_STRING
        self.__devicetype = EMPTY_STRING
        self.__last_command_time = int(round(time.time() * 1000))

        self.__volt_display = VOLT_UNDEFINED_VALUE

        # self.__mode = Mode.NONE
        # ---------------------------
        # limits for DELTA SM70AR24
        # ---------------------------
        self.__device_voltage_low_limit = SM70AR24_VOLTAGE_LOW_LIMIT
        self.__device_voltage_high_limit = SM70AR24_VOLTAGE_HIGH_LIMIT
        self.__device_current_low_limit = SM70AR24_CURRENT_LOW_LIMIT
        self.__device_current_high_limit = SM70AR24_CURRENT_HIGH_LIMIT
        # ---------------------------
        # application limits
        # ---------------------------
        self.__app_voltage_low_limit = voltage_low_limit
        self.__app_voltage_high_limit = voltage_high_limit
        self.__app_current_low_limit = current_low_limit
        self.__app_current_high_limit = current_high_limit
        # ---------------------------
        # human security limits
        # ---------------------------
        self.__voltage_high_limit_human_secure = HUMAN_SECURE_MAX_VOLTAGE
        self.id()
        # self.set_mode_vdc_auto_range()

    # --------------------------------------------------
    def set_app_current_limit(self, upper=SM70AR24_CURRENT_HIGH_LIMIT, lower=SM70AR24_CURRENT_LOW_LIMIT):
        if type(upper) is int or type(upper) is float and \
                type(lower) is int or type(lower) is float:

            self.__app_current_high_limit = upper
            if lower == SM70AR24_CURRENT_LOW_LIMIT and upper != SM70AR24_CURRENT_HIGH_LIMIT:
                self.__app_current_low_limit = -upper
            else:
                self.__app_current_low_limit = lower
        else:
            return

    # --------------------------------------------------
    def set_app_voltage_limit(self, upper=SM70AR24_VOLTAGE_HIGH_LIMIT, lower=SM70AR24_VOLTAGE_LOW_LIMIT):
        if type(upper) is int or type(upper) is float and \
                type(lower) is int or type(lower) is float:
            self.__app_voltage_high_limit = upper
            if lower == SM70AR24_VOLTAGE_LOW_LIMIT and upper != SM70AR24_VOLTAGE_HIGH_LIMIT:
                self.__app_voltage_low_limit = -upper
            else:
                self.__app_voltage_low_limit = lower
        else:
            return

    # --------------------------------------------------
    def __voltage_limiter(self, volt):
        # upper limits
        if volt > self.__device_voltage_high_limit:
            volt = self.__device_voltage_high_limit
        if volt > self.__app_voltage_high_limit:
            volt = self.__app_voltage_high_limit
        if volt > abs(self.__voltage_high_limit_human_secure):
            volt = abs(self.__voltage_high_limit_human_secure)
        # lower limit
        if volt < self.__device_voltage_low_limit:
            volt = self.__device_voltage_low_limit
        if volt < self.__app_voltage_low_limit:
            volt = self.__app_voltage_low_limit
        if volt < -abs(self.__voltage_high_limit_human_secure):
            volt = -abs(self.__voltage_high_limit_human_secure)
        return volt

    # --------------------------------------------------
    def __current_limiter(self, current):
        # upper limits
        if current > self.__device_current_high_limit:
            current = self.__device_current_high_limit
        if current > self.__app_current_high_limit:
            current = self.__app_current_high_limit
        # lower limit
        if current < self.__device_current_low_limit:
            current = self.__device_current_low_limit
        if current < self.__app_current_low_limit:
            current = self.__app_current_low_limit
        return current

    # --------------------------------------------------
    def connected(self):
        if self.socket is not None:
            rep = self.__send_and_receive_command("*idn?")
            if self.__serialnumber in rep:
                return True
        return False

    # --------------------------------------------------
    def __send_and_receive_command(self, command):
        command = command + "\n"
        try:
            self.socket.settimeout(SOCKET_TIMEOUT_SECONDS)
            self.socket.sendall(command.encode("UTF-8"))
            self.__last_command_time = int(round(time.time() * 1000))
            return self.socket.recv(BUFFER_SIZE).decode("UTF-8").rstrip()
        except:
            return ""

    # --------------------------------------------------
    # set value without receiving a response
    def __send_command(self, command):
        try:
            self.socket.settimeout(SOCKET_TIMEOUT_SECONDS)
            command = command + "\n"
            self.socket.sendall(command.encode("UTF-8"))
            self.__last_command_time = int(round(time.time() * 1000))
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
        try:
            return bool(self.__send_command(cmd))
        except:
            return False

    # --------------------------------------------------

    def output_off(self):
        cmd = "OUTPUT 0"
        try:
            return bool(self.__send_command(cmd))
        except:
            return False

    # --------------------------------------------------
    def __get_volt(self):
        try:
            return float(self.__send_and_receive_command("SOUR:VOLT?"))
        except:
            return VOLT_UNDEFINED_VALUE

    # --------------------------------------------------

    def __set_volt(self, voltage_to_apply):
        # we only accept int or float
        try:
            # Voltage control: "REM" remote , "LOC" local from panel
            self.__send_command("SYST:REM:CV REM")
            if type(voltage_to_apply) is int or type(voltage_to_apply) is float:
                voltage_to_apply = float(voltage_to_apply)
                voltage_to_apply = self.__voltage_limiter(voltage_to_apply)
                try:
                    self.__send_command("SOUR:VOLT {0}".format(voltage_to_apply))
                except:
                    pass
        except:
            pass

    # --------------------------------------------------
    def __get_volt_display(self):
        try:
            self.__volt_display = float(self.__send_and_receive_command("MEAS:VOLT?"))
        except:
            return VOLT_UNDEFINED_VALUE
        return self.__volt_display
    # --------------------------------------------------

    def __get_volt_display_as_string(self):
        self.__get_volt_display()
        return "{:.6f}".format(self.__volt_display) + " " + self.__get_volt_unit()
    # --------------------------------------------------

    def __get_current(self):
        try:
            return self.__send_and_receive_command("SOUR:CURR?")
        except:
            return ""

    # --------------------------------------------------

    def __set_current(self, current_to_apply):
        # we only accept int or float
        try:
            # Current control: "REM" remote , "LOC" local from panel
            self.__send_command("SYST:REM:CC REM")
            if type(current_to_apply) is int or type(current_to_apply) is float:
                current_to_apply = float(current_to_apply)
                current_to_apply = self.__voltage_limiter(current_to_apply)
                try:
                    self.__send_command("SOUR:CURR {0}".format(current_to_apply))
                except:
                    pass
        except:
            pass
    # --------------------------------------------------

    def __get_current_display(self):
        try:
            self.__current_display = float(self.__send_and_receive_command("MEAS:CURR?"))
        except:
            return CURRENT_UNDEFINED_VALUE
        return self.__current_display
        # --------------------------------------------------

    def __get_current_display_as_string(self):
        self.__get_current_display()
        return "{:.6f}".format(self.__current_display) + " " + self.__get_current_unit()
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

    def __get_volt_unit(self):
        return "V"

    # --------------------------------------------------

    def __get_current_unit(self):
        return "A"

    # --------------------------------------------------

    def __get_volt_undef_value(self):
        return VOLT_UNDEFINED_VALUE

    # --------------------------------------------------

    def __get_current_undef_value(self):
        return CURRENT_UNDEFINED_VALUE

    # ----------------------
    # Interface to the world
    # ----------------------
    apply_volt = property(__get_volt, __set_volt)
    volt = property(__get_volt_display)
    volt_as_string = property(__get_volt_display_as_string)
    volt_unit = property(__get_volt_unit)
    volt_undef_value = property(__get_volt_undef_value)
    # -------------------------------------------------------------
    apply_current = property(__get_current, __set_current)
    current = property(__get_current_display)
    current_as_string = property(__get_current_display_as_string)
    current_unit = property(__get_current_unit)
    current_undef_value = property(__get_current_undef_value)
    # -------------------------------------------------------------
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
