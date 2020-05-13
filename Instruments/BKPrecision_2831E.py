import serial
import time
import enum

# Messung der Periode fehlt noch

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


class Mode (enum.Enum):
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
    def __init__(self, port, baudrate=BK2831E_DEFAULT_BAUDRATE):
        # open serial connection
        # open serial connection
        try:
            self.__ser = serial.Serial(port, baudrate)
            self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
        except:
            print("ERR - COULD NOT CONNECT")
            raise
        self.__idstring = EMPTY_BYTE_STRING
        self.__serialnumber = EMPTY_BYTE_STRING
        self.__model = EMPTY_BYTE_STRING
        self.__manufactorer = EMPTY_BYTE_STRING
        self.__devicetype = EMPTY_BYTE_STRING
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

        self.__mode = Mode.NONE
        self.id()

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
            time.sleep(0.01)
        self.__last_command_time = int(round(time.time() * 1000))

    # --------------------------------------------------
    def __send_command(self, cmd):
        self.__wait_minimal_command_interval(MINIMUM_TIME_IN_MS_BETWEEN_COMMANDS)
        if not isinstance(cmd, bytes):
            return False
        if len(cmd) <= 0:
            return False
        try:
            cmd = cmd.decode("utf-8")
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
                    # print("TIMOUR")
                    return False
        except:
            return False
        # print("OK")
        return True

    # --------------------------------------------------
    def id(self):
        try:
            if self.__send_command(b'*idn?\n'):
                self.__idstring = self.__ser.readline()
                _t = self.__idstring.split(b',')
                self.__model = _t[0].split(b" ")[0]
                self.__manufactorer = b"BK Precision"
                self.__serialnumber = _t[2].replace(b'\n', b'')
                self.__serialnumber = self.__serialnumber.replace(b'\r', b'')
                self.__devicetype = b'Multimeter'
                # Initialise system
                n_lpc = str(NLPC_DEFAULT).encode("utf-8")
                self.__send_command(b'volt:dc:nplc ' + n_lpc + b'\n')
                self.__send_command(b'volt:ac:nplc ' + n_lpc + b'\n')
                self.__send_command(b'curr:dc:nplc ' + n_lpc + b'\n')
                self.__send_command(b'curr:ac:nplc ' + n_lpc + b'\n')
            else:
                raise
        except:
            self.__model = EMPTY_BYTE_STRING
            self.__manufactorer = EMPTY_BYTE_STRING
            self.__serialnumber = EMPTY_BYTE_STRING
        if self.__model == EMPTY_BYTE_STRING:
            print("ERR - NO RESPONSE")
            raise

    # --------------------------------------------------
    def set_mode_vdc_auto_range(self):
        try:
            self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
            self.__send_command(b'func volt:DC\n')
            self.__send_command(b':volt:dc:rang:auto ON\n')
            self.__mode = Mode.VOLT_METER_DC
            return True
        except:
            self.__mode = Mode.NONE
            return False

    # --------------------------------------------------
    def set_mode_vac_auto_range(self):
        try:
            self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
            self.__send_command(b'func volt:AC\n')
            self.__send_command(b':volt:ac:rang:auto ON\n')
            self.__mode = Mode.VOLT_METER_AC
            return True
        except:
            self.__mode = Mode.NONE
            return False

    # --------------------------------------------------
    def set_mode_idc_range_200mA(self):
        try:
            self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
            #self.__send_command(b':curr:dc:rang:auto OFF\n')
            self.__send_command(b'func curr:dc\n')
            self.__send_command(b':curr:dc:rang 0.2\n')
            self.__mode = Mode.AMPERE_METER_DC
            return True
        except:
            self.__mode = Mode.NONE
            return False

    # --------------------------------------------------
    def set_mode_iac_range_200mA(self):
        try:
            self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
            self.__send_command(b'func curr:AC\n')
            #self.__send_command(b':curr:ac:rang:auto OFF\n')
            self.__send_command(b':curr:ac:rang 0.2\n')

            self.__mode = Mode.AMPERE_METER_AC
            return True
        except:
            self.__mode = Mode.NONE
            return False

    # --------------------------------------------------
    def set_mode_idc_range_20A(self):
        try:
            self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
            self.__send_command(b'func curr:dc\n')
            #self.__send_command(b':curr:dc:rang:auto OFF\n')
            self.__send_command(b':curr:dc:rang 20\n')
            self.__mode = Mode.AMPERE_METER_DC
            return True
        except:
            self.__mode = Mode.NONE
            return False

    # --------------------------------------------------
    def set_mode_iac_range_20A(self):
        try:
            self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
            self.__send_command(b'func curr:AC\n')
            #self.__send_command(b':curr:ac:rang:auto OFF\n')
            self.__send_command(b':curr:ac:rang 20\n')

            self.__mode = Mode.AMPERE_METER_AC
            return True
        except:
            self.__mode = Mode.NONE
            return False

    # --------------------------------------------------
    def set_mode_resistance_auto_range(self):
        try:
            self.__ser.timeout = RECEIVE_LINE_TIMEOUT / 1000
            # if self.__mode == Mode.RESISTANCE:
            self.__send_command(b'func res\n')
            self.__send_command(b':res:rang:auto ON\n')
            self.__mode = Mode.RESISTANCE
            return True
        except:
            self.__mode = Mode.NONE
            return False

    # --------------------------------------------------
    def set_mode_frequency_auto_range(self):
        try:
            self.__ser.timeout = 2 * RECEIVE_LINE_TIMEOUT / 1000
            self.__send_command(b'func freq\n')
            self.__mode = Mode.FREQUENCE
            return True
        except:
            self.__mode = Mode.NONE
            return False

    # --------------------------------------------------
    def measure(self):
        try:
            self.__send_command(b'fetch?\n')
            res = self.__ser.readline()
            #print(res)
            try:
                value = float(res)
            except:
                value = OVERFLOW_ERROR
            self.__ser.flush()
        except:
            return
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

    def __del__(self):
        self.__ser.close()
