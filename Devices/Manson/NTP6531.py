import random
import time
from numpy import clip
import serial
import threading
import datetime

OK_BYTE_STRING = b'OK'
EMPTY_BYTE_STRING = b''
EMPTY_STRING = ""

HUMAN_SECURE_MAX_VOLTAGE = 50

COMMAND_INTERVAL_MS = 200  # minimal interval between commands in milliseconds
COMMAND_RESPONSE_TIME_MS = 200
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
            self.__ser = serial.Serial(port=port, baudrate=baudrate, timeout=0)
            serial.Serial()
        except:
            raise Exception("Serial Port " + str(port) + " - COULD NOT CONNECT")

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
        self.__last_command_time = int(round(time.time() * 1000))
        self.__lock = threading.Lock()
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
            raise

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
            raise

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
            raise

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
            raise

    # --------------------------------------------------
    def __current_limiter(self, curr):
        # limits
        curr = clip(curr, self.__device_current_low_limit, self.__device_current_high_limit)
        curr = clip(curr, self.__app_current_low_limit, self.__app_current_high_limit)
        return curr

    # --------------------------------------------------
    def __wait_minimal_command_interval(self, ms_interval=100):
        while (int(round(time.time() * 1000)) - self.__last_command_time) < ms_interval:
            time.sleep(0.01)
        self.__last_command_time = int(round(time.time() * 1000))

    # --------------------------------------------------
    def __send_command_and_receive_ok(self, cmd):
        try:
            self.__send_command_and_receive_reply_and_ok(cmd, read_reply=False)
        except:
            raise

    # --------------------------------------------------
    def __send_command_and_receive_reply_and_ok(self, cmd, read_reply=True):
        try:
            reply = bytes()
            ok = bytes()
            try:
                cmd = cmd.encode("utf-8")
            except:
                pass
            with self.__lock:
                self.__wait_minimal_command_interval(COMMAND_INTERVAL_MS)
                try:
                    for i in range(1, 11):  # 10 times trying to  read
                        # clear all bytes and chars in buffer
                        self.__ser.reset_input_buffer()
                        self.__ser.reset_output_buffer()
                        self.__ser.flush()
                        self.__ser.write(cmd)
                        # note time to calculate timeout later
                        start_wait = time.time()
                        # loop until first char is in the buffer
                        while self.__ser.in_waiting == 0:
                            time.sleep(0.025)
                            if time.time() - start_wait > (COMMAND_RESPONSE_TIME_MS / 1000.0):
                                break
                        # print(time.time() - start_wait)
                        # we need some time to read all chars until \r
                        self.__ser.timeout = 0.1
                        try:
                            # read the reply
                            if read_reply:
                                reply = self.__ser.read_until(b'\r')
                                # print(reply)
                                if b'\r' not in reply:
                                    raise Exception
                            # read the OK
                            ok = self.__ser.read_until(b'\r')
                            if b"OK\r" != ok:
                                raise Exception
                            # read all remaining chars in buffer
                            self.__ser.timeout = 0
                            self.__ser.read()
                        except:
                            # next try to execute the command
                            continue
                        # if (time.time() - start_wait) > 0.0:
                        #    print(str(datetime.datetime.now()) + " " + str(time.time() - start_wait))
                        return reply.decode("utf-8")
                    # print("Serial Timeout")
                    raise Exception("NTP6531 - Receive Timeout Error")
                except:
                    raise
        except:
            raise

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
            self.__model = self.__send_command_and_receive_reply_and_ok(b'GMOD\r').split("\r")[0]
            self.__manufactorer = "Manson"
            self.__serialnumber = str(9000 + random.randrange(999))
            self.__devicetype = "DC-Power Supply"
        except:
            self.__model = EMPTY_STRING
            self.__manufactorer = EMPTY_STRING
            self.__serialnumber = EMPTY_STRING
            self.__devicetype = EMPTY_STRING
            raise

    # --------------------------------------------------
    def output(self, s):
        try:
            state = int(bool(int(s)))
        except:
            raise
        try:
            cmd = ("SOUT" + (str(state).zfill(1)) + "\r")
            self.__send_command_and_receive_ok(cmd)
        except:
            raise

    # --------------------------------------------------
    def output_on(self):
        try:
            self.__send_command_and_receive_ok("SOUT1\r")
        except:
            raise

    # --------------------------------------------------
    def output_off(self):
        try:
            self.__send_command_and_receive_ok("SOUT0\r")
        except:
            raise

    # --------------------------------------------------
    def __get_display(self):
        try:
            res = self.__send_command_and_receive_reply_and_ok(b'GETD\r').split(";")
            try:
                self.__volt_display = float(res[0]) / 100.0
                self.__current_display = float(res[1]) / 1000.0
                self.__mode_display = int(res[2])
            except:
                raise
        except:
            raise

    # --------------------------------------------------
    def __get_volt_display(self):
        try:
            self.__get_display()
            return self.__volt_display
        except:
            raise

    # --------------------------------------------------
    def __get_volt_display_as_string(self):
        try:
            return "{:.6f}".format(self.__get_volt_display()) + " " + self.__get_volt_unit() + "DC"
        except:
            raise

    # --------------------------------------------------
    def __get_current_display(self):
        try:
            self.__get_display()
            return self.__current_display
        except:
            raise

    # --------------------------------------------------
    def __get_current_display_as_string(self):
        try:
            return "{:.6f}".format(self.__get_current_display()) + " " + self.__get_current_unit() + "DC"
        except:
            raise

    # --------------------------------------------------
    def __get_display_mode(self):
        try:
            self.__get_display()
            if self.__mode_display == 0:
                return "VC"
            if self.__mode_display == 1:
                return "CC"
            raise Exception("Invalid Data")
        except:
            raise

    # --------------------------------------------------
    def __get_applied(self):
        try:
            res = self.__send_command_and_receive_reply_and_ok(b'GETS\r').split(";")
            try:
                self.__volt_applied = float(res[0]) / 100.0
                self.__current_applied = float(res[1]) / 1000.0
            except:
                raise
        except:
            raise

    # --------------------------------------------------
    def __get_volt(self):
        try:
            self.__get_applied()
            return self.__volt_applied
        except:
            raise

    # --------------------------------------------------
    def __set_volt(self, v):
        try:
            v = float(v)
        except:
            raise
        try:
            v = self.__voltage_limiter(v)
            cmd = "VOLT" + (str(int(v * 100)).zfill(4)) + "\r"
            self.__send_command_and_receive_ok(cmd)
        except:
            raise

    # --------------------------------------------------
    def __get_current(self):
        try:
            self.__get_applied()
            return self.__current_applied
        except:
            raise

    # --------------------------------------------------
    def __set_current(self, c):
        try:
            c = float(c)
        except:
            raise
        try:
            v = self.__voltage_limiter(c)
            cmd = "CURR" + (str(int(c * 1000)).zfill(4)) + "\r"
            self.__send_command_and_receive_ok(cmd)
        except:
            raise

    # --------------------------------------------------
    def __get_power_display(self):
        try:
            self.__get_display()
            return self.__current_display * self.__volt_display
        except:
            raise

    # --------------------------------------------------
    def __get_power_display_as_string(self):
        try:
            return "{:.6f}".format(self.__get_power_display()) + " " + self.__get_power_unit() + "DC"
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

    def close(self):
        try:
            self.__ser.close()
        except:
            raise

    # ----------------------
    # Interface to the world
    # ----------------------
    apply_volt = property(__get_volt, __set_volt)
    volt = property(__get_volt_display)
    volt_as_string = property(__get_volt_display_as_string)
    volt_unit = property(__get_volt_unit)
    volt_limit_high = property(__get_volt_upper_limit, __set_volt_upper_limit)
    volt_limit_low = property(__get_volt_lower_limit, __set_volt_lower_limit)
    # -------------------------------------------------------------
    apply_current = property(__get_current, __set_current)
    current = property(__get_current_display)
    current_as_string = property(__get_current_display_as_string)
    current_unit = property(__get_current_unit)
    current_limit_high = property(__get_current_upper_limit, __set_current_upper_limit)
    current_limit_low = property(__get_current_lower_limit, __set_current_lower_limit)
    # -------------------------------------------------------------
    power = property(__get_power_display)
    power_as_string = property(__get_power_display_as_string)
    power_unit = property(__get_power_unit)
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
            raise
