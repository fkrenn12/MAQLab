from Devices.Manson.NTP6531 import NTP6531
from Devices.Keithley.SM2400 import SM2400
from Devices.BKPrecision.E2831 import BK2831E

import Devices
import time
import datetime

# ---------------------------------------------------
# be sure to make proper COM port settings
# ---------------------------------------------------
VCOMport = "com5"  # -> change to your needs


class Portmanager:
    def __init__(self):
        self.__usedports = {}

    def add(self, instrument, port):
        if port in self.__usedports:
            if self.__usedports[port] != instrument:
                # close if another instrument used port
                try:
                    self.__usedports[port].close()
                finally:
                    del self.__usedports[port]
        try:
            self.__usedports[port] = instrument
        except:
            pass



pm = Portmanager()


# istrmnt = Manson.NTP6531(VCOMport)

class Voltmeter:
    def __init__(self, instrument_name, port):
        # isinstance()
        if type(instrument_name) is str:
            pm.add(self, port)
            self.__name = instrument_name
            # print(globals())
            self.__comport = port
            self.__dev = globals()[self.__name](port)

    def __get_volt(self):
        if self.__dev is not None:
            return self.__dev.volt

    def on(self):
        self.__dev.output_on()

    def close(self):
        self.__dev.close()

    volt = property(__get_volt)


# isinstance()
class VoltageSource:
    def __init__(self, instrument_name, port):
        # isinstance()
        if type(instrument_name) is str:
            pm.add(self, port)
            self.__name = instrument_name
            # print(globals())
            self.__comport = port
            self.__dev = globals()[self.__name](port)

    def __get_volt(self):
        if self.__dev is not None:
            return self.__dev.volt

    def __set_volt(self, v):
        if self.__dev is not None:
            self.__dev.apply_volt = v

    def on(self):
        self.__dev.output_on()

    def off(self):
        self.__dev.output_off()

    def power(self):
        return self.__dev.power

    def close(self):
        self.__dev.close()

    volt = property(__get_volt, __set_volt)


u1 = VoltageSource("NTP6531", "com5")

while True:
    u1.on()
    for v in range(1,10):
        print("Set to: " +str(v))
        u1.volt = v
        time.sleep(0.2)
        print(u1.volt)
        print(u1.power())
    u1.off()
    time.sleep(1)


time.sleep(2)
v1 = Voltmeter("NTP6531", "com5")
print(str(datetime.datetime.now()) + " " + str(v1.volt))
v3 = Voltmeter("NTP6531", "com5")
print(str(datetime.datetime.now()) + " " + str(v3.volt))
time.sleep(5)

u2 = VoltageSource("NTP6531", "com5")
u2.volt = 1
time.sleep(5)
print(u2.volt)
'''
NTP = Manson_NTP6531.NTP6531(VCOMport)

print(NTP.devicetype)
print(NTP.manufactorer)
print(NTP.serialnumber)
print(NTP.model)

NTP.set_voltage_limit(10)
NTP.set_current_limit(2)
NTP.apply_current = 1.1  # strombegrenzung
for i in range(1, 10):
    NTP.output(True)
    time.sleep(0.3)
    NTP.output(False)
    time.sleep(0.3)

NTP.output_on()

for i in range(20, 300, 5):
    NTP.apply_volt = i / 10
    time.sleep(3)  # wait for voltage setting / 2sec is a good valu2
    print(str(NTP.apply_volt) + ":" + NTP.current_as_string + "  " + NTP.volt_as_string + " " + NTP.source_mode)

NTP.output_off()
'''
