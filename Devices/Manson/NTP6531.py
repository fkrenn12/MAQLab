import random
import time
from numpy import clip
import serial

OK_BYTE_STRING = b'OK'
EMPTY_BYTE_STRING = b''
EMPTY_STRING = ""

HUMAN_SECURE_MAX_VOLTAGE = 50
VOLT_UNDEFINED_VALUE = -999999.99
CURRENT_UNDEFINED_VALUE = -999999.99

TIMEOUT = 200  # serial read time in milliseconds of a line
DISPLAY_INTERVAL = 100  # minimal interval between display readings in milliseconds
NTP6531_DEFAULT_BAUDRATE = 9600
NTP6531_VOLTAGE_HIGH_LIMIT = 36.0
NTP6531_VOLTAGE_LOW_LIMIT = 1.0
NTP6531_CURRENT_HIGH_LIMIT = 3.30
NTP6531_CURRENT_LOW_LIMIT = 0.250


# --------------------------------------------------
class NTP6531:
    # --------------------------------------------------
    # Class Constructor
    # --------------------------------------------------
    def __init__(self, port,
                 baudrate=NTP6531_DEFAULT_BAUDRATE,
                 voltage_low_limit=NTP6531_VOLTAGE_LOW_LIMIT,
                 voltage_high_limit=NTP6531_VOLTAGE_HIGH_LIMIT,
                 current_low_limit=NTP6531_CURRENT_LOW_LIMIT,
                 current_high_limit=NTP6531_CURRENT_HIGH_LIMIT):

        # open serial connection
        try:
            self.__ser = serial.Serial(port, baudrate)
        except:
            print("ERR - COULD NOT CONNECT")
            raise
        self.__serialnumber = EMPTY_BYTE_STRING
        self.__model = EMPTY_BYTE_STRING
        self.__manufactorer = EMPTY_BYTE_STRING
        self.__devicetype = EMPTY_BYTE_STRING
        self.__last_measure_tic = 0
        self.__volt_display = 0.0
        self.__current_display = 0.0
        self.__mode_display = 0
        self.__volt_applied = 0
        self.__current_setting = 0
        # ---------------------------
        # limits for MANSON NTP-6531
        # ---------------------------
        self.__device_voltage_low_limit = NTP6531_VOLTAGE_LOW_LIMIT
        self.__device_voltage_high_limit = NTP6531_VOLTAGE_HIGH_LIMIT
        self.__device_current_low_limit = NTP6531_CURRENT_LOW_LIMIT
        self.__device_current_high_limit = NTP6531_CURRENT_HIGH_LIMIT
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
            volt = clip(volt, NTP6531_VOLTAGE_LOW_LIMIT, NTP6531_VOLTAGE_HIGH_LIMIT)
            self.__app_voltage_high_limit = volt
        except:
            pass

    # --------------------------------------------------
    def __get_volt_lower_limit(self):
        return self.__app_voltage_low_limit

    # --------------------------------------------------
    def __set_volt_lower_limit(self, volt_min):
        try:
            volt_min = float(volt_min)
            volt_min = clip(volt_min, NTP6531_VOLTAGE_LOW_LIMIT, NTP6531_VOLTAGE_HIGH_LIMIT)
            self.__app_voltage_low_limit = volt_min
        except:
            pass

    # --------------------------------------------------
    def __voltage_limiter(self, volt):
        # limits
        volt = clip(volt, self.__device_voltage_low_limit, self.__device_voltage_high_limit)
        volt = clip(volt, self.__app_voltage_low_limit, self.__app_voltage_high_limit)
        volt = clip(volt, -abs(self.__voltage_high_limit_human_secure), abs(self.__voltage_high_limit_human_secure))
        return volt

    # --------------------------------------------------
    def __get_current_upper_limit(self):
        return self.__app_current_high_limit

    # --------------------------------------------------
    def __set_current_upper_limit(self, current_max):
        try:
            current_max = float(current_max)
            current_max = clip(current_max, NTP6531_CURRENT_LOW_LIMIT, NTP6531_CURRENT_HIGH_LIMIT)
            self.__app_current_high_limit = current_max
        except:
            pass

    # --------------------------------------------------
    def __get_current_lower_limit(self):
        return self.__app_current_low_limit

    # --------------------------------------------------
    def __set_current_lower_limit(self, current_min):
        try:
            current_min = float(current_min)
            current_min = clip(current_min, NTP6531_CURRENT_LOW_LIMIT, NTP6531_CURRENT_HIGH_LIMIT)
            self.__app_current_low_limit = current_min
        except:
            pass

    # --------------------------------------------------
    def __current_limiter(self, curr):
        # limits
        curr = clip(curr, self.__device_current_low_limit, self.__device_current_high_limit)
        curr = clip(curr, self.__app_current_low_limit, self.__app_current_high_limit)
        return curr
    '''
    # --------------------------------------------------
    def set_app_current_limit(self, upper=NTP6531_CURRENT_HIGH_LIMIT, lower=NTP6531_CURRENT_LOW_LIMIT):
        if type(upper) is int or type(upper) is float and \
                type(lower) is int or type(lower) is float:

            self.__app_current_high_limit = upper
            if lower == NTP6531_CURRENT_LOW_LIMIT and upper != NTP6531_CURRENT_HIGH_LIMIT:
                self.__app_current_low_limit = -upper
            else:
                self.__app_current_low_limit = lower
        else:
            return

    # --------------------------------------------------
    def set_app_voltage_limit(self, upper=NTP6531_VOLTAGE_HIGH_LIMIT, lower=NTP6531_VOLTAGE_LOW_LIMIT):
        if type(upper) is int or type(upper) is float and \
                type(lower) is int or type(lower) is float:
            self.__app_voltage_high_limit = upper
            if lower == NTP6531_VOLTAGE_LOW_LIMIT and upper != NTP6531_VOLTAGE_HIGH_LIMIT:
                self.__app_voltage_low_limit = -upper
            else:
                self.__app_voltage_low_limit = lower
        else:
            return

        # --------------------------------------------------

    def __voltage_limiter(self, volt):
        # limits
        clip(volt, self.__device_voltage_low_limit, self.__device_voltage_high_limit)
        clip(volt, self.__app_voltage_low_limit, self.__app_voltage_high_limit)
        clip(volt, -abs(self.__voltage_high_limit_human_secure), abs(self.__voltage_high_limit_human_secure))
        return volt

        # --------------------------------------------------

    def __current_limiter(self, current):
        # limits
        clip(current, self.__device_current_low_limit, self.__device_current_high_limit)
        clip(current, self.__app_current_low_limit, self.__app_current_high_limit)
        return current
    # --------------------------------------------------
    '''
    def __readline(self, timeout):
        tout = timeout
        tic = int(round(time.time() * 1000))
        buff = EMPTY_BYTE_STRING
        try:
            while (int(round(time.time() * 1000)) - tic) < tout:
                if self.__ser.in_waiting > 0:
                    c = self.__ser.read(1)
                    if c != b'\r':
                        buff += c
                    else:
                        return buff
        except:
            pass
        return EMPTY_BYTE_STRING

    # --------------------------------------------------
    def __send_command(self, cmd):
        if type(cmd) is bytes:
            try:
                for i in range(1, 11):  # 10 times trying
                    self.__ser.flush()
                    self.__ser.flushInput()
                    self.__ser.write(cmd)
                    response = self.__readline(TIMEOUT)
                    if response == OK_BYTE_STRING:
                        return True
                return False
            except:
                return False

    # --------------------------------------------------
    def disable_human_safety_mode(self):
        self.__voltage_high_limit_human_secure = NTP6531_VOLTAGE_HIGH_LIMIT

    # --------------------------------------------------
    def connected(self):
        try:
            if self.__ser.in_waiting >= 0:
                return True
        except:
            return False

    # --------------------------------------------------
    def id(self):
        try:
            idstring = EMPTY_BYTE_STRING
            for i in range(1, 11):  # 10 times trying
                self.__ser.flush()
                self.__ser.flushInput()
                self.__ser.write(b'GMOD\r')
                idstring = self.__readline(TIMEOUT)
                if len(idstring) > 0:
                    break
            t = idstring.split(b'\r')
            self.__model = t[0].decode("utf-8")
            self.__manufactorer = "Manson"
            self.__serialnumber = str(9000 + random.randrange(999))
            self.__devicetype = "DC-Power Supply"
            self.__readline(TIMEOUT)  # read remaining chars
        except:
            self.__model = EMPTY_STRING
            self.__manufactorer = EMPTY_STRING
            self.__serialnumber = EMPTY_STRING
            self.__devicetype = EMPTY_STRING
            print("ERR - NO RESPONSE")

    # --------------------------------------------------
    def output(self, s):
        if type(s) is int or type(s) is float or type(s) is bool:
            try:
                state = int(bool(int(s)))
                cmd = ("SOUT" + (str(state).zfill(1)) + "\r").encode('utf-8')
                return bool(self.__send_command(cmd))  # self.__ser.write(cmd.encode('utf-8'))
            except:
                return False

    # --------------------------------------------------
    def output_on(self):
        cmd = b"SOUT1\r"
        return bool(self.__send_command(cmd))

    # --------------------------------------------------
    def output_off(self):
        cmd = b'SOUT0\r'
        return bool(self.__send_command(cmd))

    # --------------------------------------------------
    def __get_display(self):
        response = EMPTY_BYTE_STRING
        tic = int(round(time.time() * 1000))
        #  check minimal call time interval
        if (tic - self.__last_measure_tic) < DISPLAY_INTERVAL:
            return response
        try:
            for i in range(1, 11):  # 10 times trying
                self.__ser.flushInput()
                cmd = b'GETD\r'
                self.__ser.write(cmd)
                response = self.__readline(TIMEOUT)
                if len(response) > 0:
                    self.__readline(TIMEOUT)  # OK kann noch gecheckt werden
                    if len(response) > 0:
                        break
        except:
            return EMPTY_BYTE_STRING

        self.__last_measure_tic = int(round(time.time() * 1000))
        if len(response) > 0:
            res = response.split(b';')
            try:
                self.__volt_display = float(res[0]) / 100.0
                self.__current_display = float(res[1]) / 1000.0
                self.__mode_display = int(res[2])
            except:
                pass

        return response

    # --------------------------------------------------
    def __get_volt_display(self):
        self.__get_display()
        return self.__volt_display

    # --------------------------------------------------
    def __get_volt_display_as_string(self):
        self.__get_display()
        return "{:.6f}".format(self.__volt_display) + " " + self.__get_volt_unit() + "DC"

    # --------------------------------------------------
    def __get_current_display(self):
        self.__get_display()
        return self.__current_display
        pass

    # --------------------------------------------------
    def __get_current_display_as_string(self):
        self.__get_display()
        return "{:.6f}".format(self.__current_display) + " " + self.__get_current_unit() + "DC"

    # --------------------------------------------------
    def __get_display_mode(self):
        self.__get_display()
        if self.__mode_display == 0:
            return "VC"
        if self.__mode_display == 1:
            return "CC"
        return ""

    # --------------------------------------------------
    def __get_applied(self):
        response = EMPTY_BYTE_STRING
        tic = int(round(time.time() * 1000))
        #  check minimal call time interval
        if (tic - self.__last_measure_tic) < DISPLAY_INTERVAL:
            return response
        try:
            for i in range(1, 11):  # 10 times trying
                self.__ser.flushInput()
                cmd = b'GETS\r'
                self.__ser.write(cmd)
                response = self.__readline(TIMEOUT)
                if len(response) > 0:
                    self.__readline(TIMEOUT)  # OK kann noch gecheckt werden
                    if len(response) > 0:
                        break
        except:
            return EMPTY_BYTE_STRING

        self.__last_measure_tic = int(round(time.time() * 1000))
        if len(response) > 0:
            res = response.split(b';')
            try:
                self.__volt_applied = float(res[0]) / 100.0
                self.__current_applied = float(res[1]) / 1000.0
            except:
                pass

        return response

    # --------------------------------------------------
    def __get_volt(self):
        self.__get_applied()
        return self.__volt_applied

    # --------------------------------------------------
    def __set_volt(self, v):
        # we only accept int or float
        if type(v) is int or type(v) is float:
            v = float(v)
            v = self.__voltage_limiter(v)
            try:
                for i in range(1, 11):  # 10 times trying
                    self.__ser.flush()
                    self.__ser.flushInput()
                    cmd = "VOLT" + (str(int(v * 100)).zfill(4)) + "\r"
                    self.__ser.write(cmd.encode('utf-8'))
                    response = self.__readline(TIMEOUT)
                    # print(response)
                    if response == OK_BYTE_STRING:
                        self.__volt_applied = v
                        break
                return
            except:
                return

    # --------------------------------------------------
    def __get_current(self):
        self.__get_applied()
        return self.__current_applied

    def __set_current(self, c):
        # we only accept int or float
        if type(c) is int or type(c) is float:
            c = float(c)
            c = self.__current_limiter(c)
            try:
                for i in range(1, 10):  # 10 Versuche da das NTP-6531 manchmal nichts zurückschickt
                    self.__ser.flush()
                    self.__ser.flushInput()
                    cmd = "CURR" + (str(int(c * 1000)).zfill(4)) + "\r"
                    self.__ser.write(cmd.encode('utf-8'))
                    response = self.__readline(TIMEOUT)
                    if response == OK_BYTE_STRING:
                        self.__current_applied = c
                        break
                return
            except:
                return

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

    def close(self):
        self.__ser.close()

    # ----------------------
    # Interface to the world
    # ----------------------
    apply_volt = property(__get_volt, __set_volt)
    volt = property(__get_volt_display)
    volt_as_string = property(__get_volt_display_as_string)
    volt_unit = property(__get_volt_unit)
    volt_undefined_value = property(__get_volt_undef_value)
    volt_limit_upper = property(__get_volt_upper_limit, __set_volt_upper_limit)
    volt_limit_lower = property(__get_volt_lower_limit, __set_volt_lower_limit)
    # -------------------------------------------------------------
    apply_current = property(__get_current, __set_current)
    current = property(__get_current_display)
    current_as_string = property(__get_current_display_as_string)
    current_unit = property(__get_current_unit)
    current_undefined_value = property(__get_current_undef_value)
    current_limit_upper = property(__get_current_upper_limit, __set_current_upper_limit)
    current_limit_lower = property(__get_current_lower_limit, __set_current_lower_limit)
    # ----------------------------------------------------------
    serialnumber = property(__get_serialnumber)
    manufactorer = property(__get_manufactorer)
    devicetype = property(__get_devicetype)
    model = property(__get_model)
    source_mode = property(__get_display_mode)

    # --------------------------------------------------
    # Class Destructor
    # --------------------------------------------------
    def __del__(self):
        try:
            self.__ser.close()
        except:
            pass
