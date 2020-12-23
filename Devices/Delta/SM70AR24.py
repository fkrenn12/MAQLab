import socket
import time
from numpy import clip

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

    # --------------------------------------------------
    def __get_volt_upper_limit(self):
        return self.__app_voltage_high_limit

    # --------------------------------------------------
    def __set_volt_upper_limit(self, volt):
        try:
            volt = float(volt)
            volt = clip(volt, SM70AR24_VOLTAGE_LOW_LIMIT, SM70AR24_VOLTAGE_HIGH_LIMIT)
            self.__app_voltage_high_limit = volt
        except:
            raise

    # --------------------------------------------------
    def __get_volt_lower_limit(self):
        return self.__app_voltage_low_limit

    # --------------------------------------------------
    def __set_volt_lower_limit(self, volt_min):
        try:
            volt_min = float(volt_min)
            volt_min = clip(volt_min, SM70AR24_VOLTAGE_LOW_LIMIT, SM70AR24_VOLTAGE_HIGH_LIMIT)
            self.__app_voltage_low_limit = volt_min
        except:
            raise

    # --------------------------------------------------
    def __voltage_limiter(self, volt):
        # limits
        try:
            volt = clip(volt, self.__device_voltage_low_limit, self.__device_voltage_high_limit)
            volt = clip(volt, self.__app_voltage_low_limit, self.__app_voltage_high_limit)
            volt = clip(volt, -abs(self.__voltage_high_limit_human_secure), abs(self.__voltage_high_limit_human_secure))
            return volt
        except:
            raise

    # --------------------------------------------------
    def __get_current_upper_limit(self):
        return self.__app_current_high_limit

    # --------------------------------------------------
    def __set_current_upper_limit(self, current_max):
        try:
            current_max = float(current_max)
            current_max = clip(current_max, SM70AR24_CURRENT_LOW_LIMIT, SM70AR24_CURRENT_HIGH_LIMIT)
            self.__app_current_high_limit = current_max
        except:
            raise

    # --------------------------------------------------
    def __get_current_lower_limit(self):
        return self.__app_current_low_limit

    # --------------------------------------------------
    def __set_current_lower_limit(self, current_min):
        try:
            current_min = float(current_min)
            current_min = clip(current_min, SM70AR24_CURRENT_LOW_LIMIT, SM70AR24_CURRENT_HIGH_LIMIT)
            self.__app_current_low_limit = current_min
        except:
            raise

    # --------------------------------------------------
    def __current_limiter(self, current):
        # limits
        try:
            current = clip(current, self.__device_current_low_limit, self.__device_current_high_limit)
            current = clip(current, self.__app_current_low_limit, self.__app_current_high_limit)
            return current
        except:
            raise

    # --------------------------------------------------
    def connected(self):
        try:
            if self.socket is not None:
                # rep = self.__send_and_receive_command("STAT:REG:A?")
                rep = self.__send_and_receive_command("*idn?")
                # if rep != "":
                #    return True
                if self.__serialnumber in rep:
                    return True
            return False
        except:
            return False

    # --------------------------------------------------
    def __send_and_receive_command(self, command):
        command = command + "\n"
        try:
            self.socket.settimeout(SOCKET_TIMEOUT_SECONDS)
            self.socket.sendall(command.encode("UTF-8"))
            self.__last_command_time = int(round(time.time() * 1000))
            received = self.socket.recv(BUFFER_SIZE)
            try:
                received = received.decode("UTF-8").rstrip()
            except:
                raise
            return received
        except:
            raise

    # --------------------------------------------------
    # set value without receiving a response
    def __send_command(self, command):
        # self.__wait_minimal_command_interval(100)
        try:
            self.socket.settimeout(SOCKET_TIMEOUT_SECONDS)
            command = command + "\n"
            self.socket.sendall(command.encode("UTF-8"))
            self.__last_command_time = int(round(time.time() * 1000))
            return True
        except:
            raise

    # --------------------------------------------------
    def disable_human_safety_mode(self):
        self.__voltage_high_limit_human_secure = SM70AR24_VOLTAGE_HIGH_LIMIT

    # --------------------------------------------------
    def __wait_minimal_command_interval(self, ms_interval=100):
        while (int(round(time.time() * 1000)) - self.__last_command_time) < ms_interval:
            time.sleep(0.02)
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
                self.__devicetype = "DC-Power Supply"
                # Initialise system
            else:
                raise
        except:
            self.__model = EMPTY_BYTE_STRING
            self.__manufactorer = EMPTY_BYTE_STRING
            self.__serialnumber = EMPTY_BYTE_STRING
            raise

    # --------------------------------------------------
    def output_on(self):
        try:
            self.__send_command("OUTPUT 1")
        except:
            raise

    # --------------------------------------------------
    def output_off(self):
        try:
            self.__send_command("OUTPUT 0")
        except:
            raise

    # --------------------------------------------------
    def __get_volt(self):
        try:
            return float(self.__send_and_receive_command("SOUR:VOLT?"))
        except:
            raise

    # --------------------------------------------------
    def __set_volt(self, voltage_to_apply):
        # we only accept int or float
        try:
            # Voltage control: "REM" remote , "LOC" local from panel
            cv_status = self.__send_and_receive_command("SYST:REM:CV?")
            if "LOC" in cv_status:
                self.__send_command("SYST:REM:CV REM")
            try:
                voltage_to_apply = float(voltage_to_apply)
                voltage_to_apply = self.__voltage_limiter(voltage_to_apply)
            except:
                raise
            try:
                self.__send_command("SOUR:VOLT {0}".format(voltage_to_apply))
            except:
                raise
        except:
            raise

    # --------------------------------------------------
    def __get_volt_display(self):
        try:
            return float(self.__send_and_receive_command("MEAS:VOLT?"))
        except:
            raise


    # --------------------------------------------------
    def __get_volt_display_as_string(self):
        try:
            return "{:.6f}".format(self.__get_volt_display()) + " " + self.__get_volt_unit() + "DC"
        except:
            raise

    # --------------------------------------------------
    def __get_current(self):
        try:
            return float(self.__send_and_receive_command("SOUR:CURR?"))
        except:
            raise

    # --------------------------------------------------
    def __set_current(self, current_to_apply):
        # we only accept int or float
        try:
            # Current control: "REM" remote , "LOC" local from panel
            cc_status = self.__send_and_receive_command("SYST:REM:CC?")
            if "LOC" in cc_status:
                self.__send_command("SYST:REM:CC REM")
            try:
                current_to_apply = float(current_to_apply)
                current_to_apply = self.__current_limiter(current_to_apply)
            except:
                raise
            try:
                self.__send_command("SOUR:CURR {0}".format(current_to_apply))
            except:
                raise
        except:
            raise

    # --------------------------------------------------

    def __get_current_display(self):
        try:
            return float(self.__send_and_receive_command("MEAS:CURR?"))
        except:
            raise

    # --------------------------------------------------

    def __get_current_display_as_string(self):
        return "{:.6f}".format(self.__get_current_display()) + " " + self.__get_current_unit() + "DC"


    # --------------------------------------------------
    def __get_power_display(self):
        try:
            return float(self.__get_current_display() * self.__get_volt_display())
        except:
            raise

    # --------------------------------------------------
    def __get_power_display_as_string(self):
        try:
            return "{:.6f}".format(self.__get_power_display) + " " + self.__get_current_unit() + "DC"
        except:
            raise

    # --------------------------------------------------
    def __del__(self):
        try:
            self.socket.close()
        except:
            raise

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
    def __get_power_unit(self):
        return "W"

    # ----------------------
    # Interface to the world
    # ----------------------
    apply_volt = property(__get_volt, __set_volt)
    volt = property(__get_volt_display)
    volt_as_string = property(__get_volt_display_as_string)
    volt_unit = property(__get_volt_unit)
    volt_limit_upper = property(__get_volt_upper_limit, __set_volt_upper_limit)
    volt_limit_lower = property(__get_volt_lower_limit, __set_volt_lower_limit)
    # -------------------------------------------------------------
    apply_current = property(__get_current, __set_current)
    current = property(__get_current_display)
    current_as_string = property(__get_current_display_as_string)
    current_unit = property(__get_current_unit)
    current_limit_upper = property(__get_current_upper_limit, __set_current_upper_limit)
    current_limit_lower = property(__get_current_lower_limit, __set_current_lower_limit)
    # -------------------------------------------------------------
    power = property(__get_power_display)
    power_as_string = property(__get_power_display_as_string)
    power_unit = property(__get_power_unit)
    # -------------------------------------------------------------
    serialnumber = property(__get_serialnumber)
    manufactorer = property(__get_manufactorer)
    devicetype = property(__get_devicetype)
    model = property(__get_model)

