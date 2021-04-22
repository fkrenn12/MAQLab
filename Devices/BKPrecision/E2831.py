import serial
import time
import enum
import threading

# TODO Messung der Periode fehlt noch

EMPTY_BYTE_STRING = b''
EMPTY_STRING = ""
RECEIVE_LINE_TIMEOUT = 1000  # serial read time in milliseconds of a line
MINIMUM_TIME_IN_MS_BETWEEN_COMMANDS = 300  # must be > 250ms
OVERFLOW_ERROR = -9999
# Set power line cycles per integration
NLPC_DEFAULT = 1
NPLC_MINIMUM = 10
NPLC_MAXIMUM = 0.1
BK2831E_DEFAULT_BAUDRATE = 9600


class Mode(enum.Enum):
    NONE = enum.auto()
    VOLT_METER_DC = enum.auto()
    VOLT_METER_AC = enum.auto()
    VOLT_METER_AC_DC = enum.auto()
    AMPERE_METER_DC = enum.auto()
    AMPERE_METER_AC = enum.auto()
    OHM_METER = enum.auto()
    FREQUENCE = enum.auto()
    PERIODE = enum.auto()
    RESISTANCE = enum.auto()


class BK2831E:
    # --------------------------------------------------
    # Class Constructor
    # --------------------------------------------------
    def __init__(self, port, baudrate=BK2831E_DEFAULT_BAUDRATE):
        # open serial connection
        try:
            self.__ser = serial.Serial(port, baudrate)
            self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
        except:
            raise Exception("Serial Port " + str(port) + " - COULD NOT CONNECT")
        self.__minimum_time_between_commands = MINIMUM_TIME_IN_MS_BETWEEN_COMMANDS
        self.__idstring = EMPTY_STRING
        self.__serialnumber = EMPTY_STRING
        self.__model = EMPTY_STRING
        self.__manufactorer = EMPTY_STRING
        self.__devicetype = EMPTY_STRING
        self.__last_current = 0
        self.__last_voltage = 0
        self.__last_resistance = 0
        self.__last_frequence = 0
        self.__last_periode = 0
        self.__last_current_unit = ""
        self.__last_voltage_unit = ""
        self.__last_resistance_unit = ""
        self.__last_frequence_unit = ""
        self.__last_periode_unit = ""
        self.__last_command_time = int(round(time.time() * 1000))
        self.__lock = threading.Lock()
        self.__mode = Mode.NONE
        self.id()
        self.set_mode_vdc_auto_range()

    # --------------------------------------------------
    def connected(self):
        try:
            if self.__ser.in_waiting >= 0:
                return True
        except:
            return False

    # --------------------------------------------------
    def __wait_minimal_command_interval(self, ms_interval):

        while (int(round(time.time() * 1000)) - self.__last_command_time) < ms_interval:
            # print("*")
            time.sleep(0.01)
        self.__last_command_time = int(round(time.time() * 1000))

    # --------------------------------------------------
    def __send_command(self, cmd):

        print(cmd)
        if cmd == "f?":
            self.__minimum_time_between_commands = 1000
        else:
            self.__minimum_time_between_commands = MINIMUM_TIME_IN_MS_BETWEEN_COMMANDS

        self.__wait_minimal_command_interval(self.__minimum_time_between_commands)

        try:
            cmd = cmd.decode("utf-8")
        except:
            pass
        if cmd == "f?":
            self.__minimum_time_between_commands = 1000
        else:
            self.__minimum_time_between_commands = MINIMUM_TIME_IN_MS_BETWEEN_COMMANDS
        # with self.__lock:
        try:
            # print(cmd)
            tout = RECEIVE_LINE_TIMEOUT
            buff = EMPTY_BYTE_STRING
            self.__ser.flush()
            # sending byte per byte and receiving it
            for char in str(cmd):
                char = char.encode("utf-8")
                self.__ser.write(char)
                tic = int(round(time.time() * 1000))
                while (int(round(time.time() * 1000)) - tic) < tout:
                    if self.__ser.in_waiting > 0:
                        ret_char = self.__ser.read(1)
                        # print(ret_char, char)
                        if ret_char == char:
                            break
                if (int(round(time.time() * 1000)) - tic) < tout:
                    continue
                else:
                    print("ERROR")
                    raise Exception("E2831 - Response CHAR " + str(cmd) + " Timeout Error")
                    # continue
        except:
            raise

    # --------------------------------------------------
    def id(self):
        try:
            self.__send_command(b'*RST\n')
            while True:
                time.sleep(2)
                try:
                    self.__send_command(b'*idn?\n')
                    self.__idstring = self.__ser.readline().decode("utf-8")
                    if "," in self.__idstring:
                        break
                except:
                    pass
            _t = self.__idstring.split(",")
            self.__model = _t[0].split(" ")[0]
            self.__manufactorer = "BK Precision"
            self.__serialnumber = _t[2].replace("\n", '')
            self.__serialnumber = self.__serialnumber.replace('\r', '')
            self.__devicetype = "Multimeter"
            # Initialise system

            n_lpc = str(NLPC_DEFAULT).encode("utf-8")
            self.__send_command(b'volt:dc:nplc ' + n_lpc + b'\n')
            self.__send_command(b'volt:ac:nplc ' + n_lpc + b'\n')
            self.__send_command(b'curr:dc:nplc ' + n_lpc + b'\n')
            self.__send_command(b'curr:ac:nplc ' + n_lpc + b'\n')
        except:
            self.__model = EMPTY_BYTE_STRING
            self.__manufactorer = EMPTY_BYTE_STRING
            self.__serialnumber = EMPTY_BYTE_STRING
            raise

    # --------------------------------------------------
    def set_mode_vdc_auto_range(self, force=False):
        try:
            if force or self.__mode != Mode.VOLT_METER_DC:
                self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
                self.__send_command(b'func volt:DC\n')
                if self.__mode == Mode.FREQUENCE or self.__mode == Mode.RESISTANCE:
                    time.sleep(0.6)
                self.__send_command(b':volt:dc:rang:auto ON\n')  # :
                self.__mode = Mode.VOLT_METER_DC
            return
        except:
            self.__mode = Mode.NONE
            raise

    # --------------------------------------------------
    def set_mode_vac_auto_range(self, force=False):
        try:
            if force or self.__mode != Mode.VOLT_METER_AC:
                self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
                self.__send_command(b'func volt:AC\n')
                self.__send_command(b':volt:ac:rang:auto ON\n')
                self.__mode = Mode.VOLT_METER_AC
            return
        except:
            self.__mode = Mode.NONE
            raise

    # --------------------------------------------------
    def set_mode_idc_range_200mA(self, force=False):
        try:
            if force or self.__mode != Mode.AMPERE_METER_DC:
                self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
                # self.__send_command(b':curr:dc:rang:auto OFF\n')
                self.__send_command(b'func curr:dc\n')
                self.__send_command(b':curr:dc:rang 0.2\n')
                self.__mode = Mode.AMPERE_METER_DC
            return
        except:
            self.__mode = Mode.NONE
            raise

    # --------------------------------------------------
    def set_mode_iac_range_200mA(self, force=False):
        try:
            if force or self.__mode != Mode.AMPERE_METER_AC:
                self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
                self.__send_command(b'func curr:AC\n')
                # self.__send_command(b':curr:ac:rang:auto OFF\n')
                self.__send_command(b':curr:ac:rang 0.2\n')
                self.__mode = Mode.AMPERE_METER_AC
            return
        except:
            self.__mode = Mode.NONE
            raise

    # --------------------------------------------------
    def set_mode_idc_range_20A(self, force=False):
        try:
            if force or self.__mode != Mode.AMPERE_METER_DC:
                self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
                self.__send_command(b'func curr:dc\n')
                # self.__send_command(b':curr:dc:rang:auto OFF\n')
                self.__send_command(b':curr:dc:rang 20\n')
                self.__mode = Mode.AMPERE_METER_DC
            return
        except:
            self.__mode = Mode.NONE
            raise

    # --------------------------------------------------
    def set_mode_iac_range_20A(self, force=False):
        try:
            if force or self.__mode != Mode.AMPERE_METER_AC:
                self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
                self.__send_command(b'func curr:AC\n')
                # self.__send_command(b':curr:ac:rang:auto OFF\n')
                self.__send_command(b':curr:ac:rang 20\n')
                self.__mode = Mode.AMPERE_METER_AC
            return
        except:
            self.__mode = Mode.NONE
            raise

    # --------------------------------------------------
    def set_mode_resistance_auto_range(self, force=False):
        try:
            if force or self.__mode != Mode.RESISTANCE:
                self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
                # if self.__mode == Mode.RESISTANCE:
                self.__send_command(b'func res\n')
                self.__send_command(b':res:rang:auto ON\n')
                self.__mode = Mode.RESISTANCE
                return
        except:
            self.__mode = Mode.NONE
            raise

    # --------------------------------------------------
    def set_mode_frequency_auto_range(self, force=False):
        try:
            if force or self.__mode != Mode.FREQUENCE:
                self.__ser.timeout = 2 * RECEIVE_LINE_TIMEOUT / 1000
                self.__send_command(b'func freq\n')
                self.__mode = Mode.FREQUENCE
                return
        except:
            self.__mode = Mode.NONE
            raise

    # --------------------------------------------------
    def measure(self):
        try:
            self.__send_command(b'fetch?\n')
            res = self.__ser.readline()
            # print(res)
            try:
                value = float(res)
            except:
                raise Exception("E2831 - VALUE ERROR")
            self.__ser.flush()
        except:
            raise

        if self.__mode == Mode.VOLT_METER_DC:
            self.__last_voltage = value
            self.__last_voltage_unit = "VDC"
        elif self.__mode == Mode.VOLT_METER_AC:
            self.__last_voltage = value
            self.__last_voltage_unit = "VAC"
        elif self.__mode == Mode.VOLT_METER_AC_DC:
            self.__last_voltage = value
            self.__last_voltage_unit = "VACDC"
        elif self.__mode == Mode.AMPERE_METER_DC:
            self.__last_current = value
            self.__last_current_unit = "ADC"
        elif self.__mode == Mode.AMPERE_METER_AC:
            self.__last_current = value
            self.__last_current_unit = "AAC"
        elif self.__mode == Mode.RESISTANCE:
            self.__last_resistance = value
            self.__last_resistance_unit = "Ohm"
        elif self.__mode == Mode.FREQUENCE:
            self.__last_frequence = value
            self.__last_frequence_unit = "Hz"
        elif self.__mode == Mode.PERIODE:
            self.__last_periode = value
            self.__last_periode_unit = "s"

    # --------------------------------------------------
    def __get_voltage_unit(self):
        return self.__last_voltage_unit

    # --------------------------------------------------
    def __get_voltage(self):
        return self.__last_voltage

    # --------------------------------------------------

    def __get_voltage_as_string(self):
        return "{:.6f}".format(self.__last_voltage) + " " + self.__get_voltage_unit()

    # --------------------------------------------------
    def __get_current_unit(self):
        return self.__last_current_unit

    # --------------------------------------------------
    def __get_current(self):
        return self.__last_current

    # --------------------------------------------------

    def __get_current_as_string(self):
        return "{:.6f}".format(self.__last_current) + " " + self.__get_current_unit()

    # --------------------------------------------------
    def __get_resistance_unit(self):
        return self.__last_resistance_unit

    # --------------------------------------------------
    def __get_frequence_unit(self):
        return self.__last_frequence_unit

    # --------------------------------------------------
    def __get_frequence(self):
        return self.__last_frequence

    # --------------------------------------------------

    def __get_frequence_as_string(self):
        return "{:.2f}".format(self.__last_frequence) + " " + self.__get_frequence_unit()

    # --------------------------------------------------
    def __get_resistance(self):
        return self.__last_resistance

    # --------------------------------------------------

    def __get_resistance_as_string(self):
        return "{:.2f}".format(self.__last_resistance) + " " + self.__get_resistance_unit()

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

    volt = property(__get_voltage)
    volt_as_string = property(__get_voltage_as_string)
    volt_unit = property(__get_voltage_unit)
    current = property(__get_current)
    current_as_string = property(__get_current_as_string)
    current_unit = property(__get_current_unit)
    resistance = property(__get_resistance)
    resistance_unit = property(__get_resistance_unit)
    resistance_as_string = property(__get_resistance_as_string)
    frequence = property(__get_frequence)
    frequence_unit = property(__get_frequence_unit)
    frequence_as_string = property(__get_frequence_as_string)
    serialnumber = property(__get_serialnumber)
    manufactorer = property(__get_manufactorer)
    devicetype = property(__get_devicetype)
    model = property(__get_model)

    # --------------------------------------------------
    # Class Destructor
    # --------------------------------------------------
    def __del__(self):
        try:
            self.__ser.close()
        except:
            pass
