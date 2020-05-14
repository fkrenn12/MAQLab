import serial
import enum

EMPTY_BYTE_STRING = b''
EMPTY_STRING = ""

TIMEOUT = 500  # serial read time in milliseconds of a line

HUMAN_SECURE_MAX_VOLTAGE = 50.0  # Volt
DEFAULT_CURRENT_MAX = 0.5  # max Ampere in voltage source mode
DEFAULT_VOLTAGE_MAX = 20.0  # max Volt in current source mode

SM2400_POWER_MAX = 22.0  # Watt
SM2400_DEFAULT_BAUDRATE = 9600  # bit/sec
SM2400_VOLTAGE_HIGH_LIMIT = 200.0  # Volt
SM2400_VOLTAGE_LOW_LIMIT = -200.0  # Volt
SM2400_CURRENT_HIGH_LIMIT = 1.0  # Ampere
SM2400_CURRENT_LOW_LIMIT = -1.0  # Ampere


class Mode(enum.Enum):
    NONE = enum.auto()
    CONSTANT_VOLTAGE = enum.auto()
    CONSTANT_CURRENT = enum.auto()
    VOLT_METER = enum.auto()
    AMPERE_METER = enum.auto()
    OHM_METER = enum.auto()


# --------------------------------------------------
class SM2400:
    def __init__(self, port,
                 baudrate=SM2400_DEFAULT_BAUDRATE,
                 voltage_low_limit=SM2400_VOLTAGE_LOW_LIMIT,
                 voltage_high_limit=SM2400_VOLTAGE_HIGH_LIMIT,
                 current_low_limit=SM2400_CURRENT_LOW_LIMIT,
                 current_high_limit=SM2400_CURRENT_HIGH_LIMIT):

        # open serial connection
        try:
            self.__ser = serial.Serial(port, baudrate)
            self.__ser.timeout = 1
        except:
            print("ERR - COULD NOT CONNECT")
            raise

        self.__idstring = EMPTY_STRING
        self.__serialnumber = EMPTY_STRING
        self.__model = EMPTY_STRING
        self.__manufactorer = EMPTY_STRING
        self.__devicetype = EMPTY_STRING
        self.__last_volt = 0
        self.__last_current = 0
        self.__last_resistance = 0
        self.__volt_applied = 0
        self.__current_applied = 0
        self.__mode = Mode.NONE
        self.__beep = 0
        # ---------------------------
        # limits for KEITHLEY 2400 Sourcemeter
        # ---------------------------
        self.__device_voltage_low_limit = SM2400_VOLTAGE_LOW_LIMIT
        self.__device_voltage_high_limit = SM2400_VOLTAGE_HIGH_LIMIT
        self.__device_current_low_limit = SM2400_CURRENT_LOW_LIMIT
        self.__device_current_high_limit = SM2400_CURRENT_HIGH_LIMIT
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
    def set_current_limit(self, upper=SM2400_CURRENT_HIGH_LIMIT, lower=SM2400_CURRENT_LOW_LIMIT):
        if type(upper) is int or type(upper) is float and \
                type(lower) is int or type(lower) is float:
            self.__app_current_high_limit = upper

            if lower == SM2400_CURRENT_LOW_LIMIT and upper != SM2400_CURRENT_HIGH_LIMIT:
                self.__app_current_low_limit = -upper
            else:
                self.__app_current_low_limit = lower

            if self.__mode == Mode.CONSTANT_VOLTAGE:
                self.__ser.write(b':SENS:CURR:PROT ' + str(self.__current_limiter(upper)).encode("utf-8") + b'\n')
        else:
            return

    # --------------------------------------------------
    def set_voltage_limit(self, upper=SM2400_VOLTAGE_HIGH_LIMIT, lower=SM2400_VOLTAGE_LOW_LIMIT):
        if type(upper) is int or type(upper) is float and \
                type(lower) is int or type(lower) is float:

            self.__app_voltage_high_limit = upper

            if lower == SM2400_VOLTAGE_LOW_LIMIT and upper != SM2400_VOLTAGE_HIGH_LIMIT:
                self.__app_voltage_low_limit = -upper
            else:
                self.__app_voltage_low_limit = lower

            if self.__mode == Mode.CONSTANT_CURRENT:
                self.__ser.write(b':SENS:VOLT:PROT ' + str(self.__voltage_limiter(upper)).encode("utf-8") + b'\n')
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
        try:
            if self.__ser.in_waiting >= 0:
                return True
        except:
            return False

    # --------------------------------------------------
    def id(self):
        try:
            # Reads identification code
            self.__ser.write(b'*RST\n')
            self.set_beep_off()
            self.__ser.write(b'*IDN?\n')
            self.__idstring = self.__ser.readline()
            # repeated string
            # KEITHLEY INSTRUMENTS INC., MODEL nnnn, xxxxxxx, yyyyy/zzzzz /a/d
            # KEITHLEY INSTRUMENTS INC.,MODEL 2400,1033388,C27   Feb  4 2004 14:58:04/A02  /K/H
            t = self.__idstring.split(b',')
            self.__manufactorer = t[0].decode("utf-8")
            self.__model = t[1].decode("utf-8")
            self.__serialnumber = t[2].decode("utf-8")
            self.__devicetype = "Sourcemeter"
        except:
            self.__model = EMPTY_STRING
            self.__manufactorer = EMPTY_STRING
            self.__serialnumber = EMPTY_STRING
            self.__devicetype = EMPTY_STRING
        if self.__model == EMPTY_STRING:
            print("ERR - NO RESPONSE")
            raise

    def disable_human_security_mode(self):
        self.__voltage_high_limit_human_secure = SM2400_VOLTAGE_HIGH_LIMIT

        # --------------------------------------------------

    def set_output_on(self):
        try:
            self.__ser.write(b'OUTP:STAT ON\n')
        except:
            pass

    # --------------------------------------------------
    def set_output_off(self):
        try:
            self.__ser.write(b'OUTP:STAT OFF\n')
        except:
            pass

    # --------------------------------------------------
    def set_mode_voltage_source(self):
        try:
            self.__mode = Mode.CONSTANT_VOLTAGE
            # self.__ser.write(b':SOUR:FUNC VOLT;:SOUR:VOLT:RANG:AUTO ON;:SOUR:VOLT:LEV 0\n')
            self.__ser.write(b':SOUR:FUNC VOLT\n')
            self.__ser.write(b':SOUR:VOLT:RANG:AUTO ON\n')
            self.__ser.write(b':SOUR:VOLT:LEV 0\n')
            self.__ser.write(b':SENS:CURR:PROT ' +
                             str(self.__current_limiter(self.__app_current_high_limit)).encode("utf-8") + b'\n')
            self.__ser.write(b':FUNC "VOLT","CURR"\n')  # neu
            self.set_output_on()
        except:
            self.__mode = Mode.NONE

    # --------------------------------------------------
    def set_mode_voltage_source_2wire(self):
        self.set_mode_voltage_source()

    # --------------------------------------------------
    def set_mode_voltage_source_4wire(self):
        self.set_mode_voltage_source()
        try:
            self.__ser.write(b':SYST:RSEN ON\n')
            self.set_output_on()
        except:
            pass

    # --------------------------------------------------
    def __get_voltage(self):
        return self.__last_volt

    # --------------------------------------------------
    def __get_voltage_as_string(self):
        return "{:.6f}".format(self.__last_volt) + " " + self.__get_volt_unit()

    # --------------------------------------------------
    def __get_apply_voltage(self):
        return self.__volt_applied

    # --------------------------------------------------
    def __set_apply_voltage(self, volt):
        if type(volt) is int or type(volt) is float:
            _old_applied = self.__volt_applied
            try:
                self.__volt_applied = self.__voltage_limiter(volt)
                # :SOURce[1]:CURRent[:LEVel][:IMMediate][:AMPLitude] <n> Set fixed I-Source amplitude immediately

                if self.__mode == Mode.CONSTANT_VOLTAGE:
                    self.__ser.write(b'SOUR:VOLT:LEV:IMM:AMPL ' + str(self.__volt_applied).encode("utf-8") + b'\n')

                elif self.__mode == Mode.CONSTANT_CURRENT:
                    self.__ser.write(b':SENS:VOLT:PROT ' + str(self.__volt_applied).encode("utf-8") + b'\n')
            except:
                self.__volt_applied = _old_applied

    # --------------------------------------------------
    def set_mode_current_source(self):
        try:
            # Model 2400: 21V @ 1.05A or 210V @ 105mA
            self.__mode = Mode.CONSTANT_CURRENT
            self.__ser.write(b'*RST\n')
            self.__set_beep(self.__beep)
            # TODO: negative limits
            # self.__current_low_limit = current_min
            self.__ser.write(b':SOURCE:FUNC:MODE CURR \n')
            self.__ser.write(b':SOURCE:CURR:RANG 100E-3 \n')
            self.__ser.write(b':SOURCE:CURR:RANG:AUTO ON\n')
            # self.__ser.write(b':SOURCE:CURR:LEV -100.000E-3 \n')
            self.__ser.write(b':SOURCE:CURR:LEV 0.000E-3 \n')  # set to 0
            self.__ser.write(b':SOURCE:CURR:MODE FIXED \n')
            self.__ser.write(b':SENS:FUNC:OFF:ALL \n')
            self.__ser.write(b':SENS:FUNC "VOLT" ,"CURR" \n')
            self.__ser.write(b':VOLT:RANG:AUTO ON\n')
            self.__ser.write(b':VOLT:PROT ' +
                             str(self.__voltage_limiter(self.__app_voltage_high_limit)).encode("utf-8") + b'\n')
            self.set_output_on()
        except:
            self.__mode = Mode.NONE

    # --------------------------------------------------
    def set_mode_current_source_2wire(self, current_max, volt_max=DEFAULT_VOLTAGE_MAX):
        self.set_mode_current_source()

    # --------------------------------------------------
    def set_mode_current_source_4wire(self, current_max, volt_max=DEFAULT_VOLTAGE_MAX):
        self.set_mode_current_source()
        try:
            self.__ser.write(b':SYST:RSEN ON\n')
            self.set_output_on()
        except:
            pass

    # --------------------------------------------------
    def __get_current(self):
        return self.__last_current

    # --------------------------------------------------
    def __get_current_as_string(self):
        return "{:.6f}".format(self.__last_current) + " " + self.__get_current_unit()

    # --------------------------------------------------
    def __get_apply_current(self):
        return self.__current_applied

    # --------------------------------------------------
    def __set_apply_current(self, current):
        if type(current) is int or type(current) is float:
            _old_applied = self.__current_applied
            try:
                self.__current_applied = self.__current_limiter(current)

                if self.__mode == Mode.CONSTANT_CURRENT:
                    # :SOURce[1]:CURRent[:LEVel][:IMMediate][:AMPLitude] <n> Set fixed I-Source amplitude immediately
                    self.__ser.write(b'SOUR:CURR:LEV:IMM:AMPL ' + str(self.__current_applied).encode("utf-8") + b'\n')
                elif self.__mode == Mode.CONSTANT_VOLTAGE:
                    self.__ser.write(b':SENS:CURR:PROT ' + str(self.__current_applied).encode("utf-8") + b'\n')
            except:
                self.__current_applied = _old_applied

    # --------------------------------------------------
    def set_mode_volt_meter(self):
        try:
            self.__mode = Mode.VOLT_METER
            self.__ser.write(b':SOUR:FUNC CURR\n')
            self.__ser.write(b':SOUR:CURR:MODE FIXED\n')
            self.__ser.write(b':SOUR:CURR:RANG MIN\n')
            self.__ser.write(b':SOUR:CURR:LEV 0\n')
            self.__ser.write(b':SENS:VOLT:PROT 200\n')  # '+str(_volt_protect).encode("utf-8")+b'\n')
            self.__ser.write(b':FUNC "VOLT","CURR"\n')
            self.__ser.write(b':SENS:VOLT:RANG 200\n')
            self.set_output_on()
        except:
            self.__mode = Mode.NONE

    # --------------------------------------------------
    def set_mode_ampere_meter(self):
        try:
            self.__mode = Mode.AMPERE_METER
            self.__ser.write(b':SOUR:FUNC VOLT\n')
            self.__ser.write(b':SOUR:VOLT:MODE FIXED\n')
            self.__ser.write(b':SOUR:VOLT:RANG MIN\n')
            self.__ser.write(b':SOUR:VOLT:LEV 0\n')
            self.__ser.write(b':SENS:CURR:PROT  1\n')  # + str(_curr_protect).encode("utf-8") + b'\n')
            self.__ser.write(b':FUNC "VOLT","CURR"\n')
            self.__ser.write(b':SENS:CURR:RANG 1\n')
            self.set_output_on()
        except:
            self.__mode = Mode.NONE

    # --------------------------------------------------
    def set_mode_ohmmeter_2wire(self):
        try:
            self.__mode = Mode.OHM_METER
            self.__ser.write(b'*RST\n')
            self.__set_beep(self.__beep)
            self.__ser.write(b'FUNC "RES"\n')
            self.__ser.write(b'RES:MODE AUTO\n')
            self.__ser.write(b'RES:RANG:AUTO ON\n')
            self.__ser.write(b':SYST:RSEN OFF\n')
            self.__ser.write(b':CONF:RES\n')
            self.set_output_on()
        except:
            self.__mode = Mode.NONE

    # --------------------------------------------------
    def set_mode_ohmmeter_4wire(self):
        try:
            self.__mode = Mode.OHM_METER
            self.__ser.write(b'*RST\n')
            self.__set_beep(self.__beep)
            self.__ser.write(b'FUNC "RES"\n')
            self.__ser.write(b'RES:MODE AUTO\n')
            self.__ser.write(b'RES:RANG:AUTO ON\n')
            self.__ser.write(b':SYST:RSEN ON\n')
            self.__ser.write(b':CONF:RES\n')
            self.set_output_on()
        except:
            self.__mode = Mode.NONE

    # --------------------------------------------------
    def __set_beep(self, on_off):
        if type(on_off) is int or type(on_off) is float or type(on_off) is bool:
            on_off = int(bool(int(on_off)))
            try:
                if on_off == 0:
                    self.__ser.write(b':SYST:BEEP:STAT OFF\n')
                    self.__beep = 0
                else:
                    self.__ser.write(b':SYST:BEEP:STAT ON\n')
                    self.__beep = 1
            except:
                pass
            return

    # --------------------------------------------------
    def set_beep_on(self):
        try:
            self.__ser.write(b':SYST:BEEP:STAT ON\n')
            self.__beep = 1
        except:
            pass
        return

    # --------------------------------------------------
    def set_beep_off(self):
        try:
            self.__ser.write(b':SYST:BEEP:STAT OFF\n')
            self.__beep = 0
        except:
            pass
        return

    # --------------------------------------------------
    def __get_value(self):
        old_last_volt = self.__last_volt
        old_last_current = self.__last_current
        old_last_resistance = self.__last_resistance
        try:
            self.__ser.write(b'READ?\n')
            res = self.__ser.readline().split(b',')
            self.__last_volt = float(res[0])
            self.__last_current = float(res[1])
            self.__last_resistance = float(res[2])
        except:
            self.__last_current = old_last_current
            self.__last_volt = old_last_volt
            self.__last_resistance = old_last_resistance
        return self.__last_volt, self.__last_current, self.__last_resistance

    # --------------------------------------------------
    def measure(self):
        self.__get_value()

    # --------------------------------------------------
    def __get_resistance(self):
        return self.__last_resistance

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
        return "VDC"

    # --------------------------------------------------
    def __get_current_unit(self):
        return "ADC"

    # --------------------------------------------------
    def __get_resistance_unit(self):
        return "Ohm"

    values = property(__get_value)
    apply_volt = property(__get_apply_voltage, __set_apply_voltage)
    volt = property(__get_voltage)
    volt_as_string = property(__get_voltage_as_string)
    volt_unit = property(__get_volt_unit)
    apply_current = property(__get_apply_current, __set_apply_current)
    current = property(__get_current)
    current_as_string = property(__get_current_as_string)
    current_unit = property(__get_current_unit)
    resistance = property(__get_resistance)
    resistance_unit = property(__get_resistance_unit)
    serialnumber = property(__get_serialnumber)
    manufactorer = property(__get_manufactorer)
    devicetype = property(__get_devicetype)
    model = property(__get_model)

    # --------------------------------------------------
    def __del__(self):
        self.__ser.close()
