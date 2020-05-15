# from Instruments.Manson import Manson_NTP6531 as Manson
import Instruments.Manson.NTP6531 as NTP6531

# ---------------------------------------------------
# be sure to make proper COM port settings
# ---------------------------------------------------
VCOMport = "com4"  # -> change to your needs

# istrmnt = Manson.NTP6531(VCOMport)

isinstance()
class Spannungsquelle():
    def __init__(self, instrument):
        isinstance()
        if type(instrument) is NTP6531.NTP6531:
            self.__dev = instrument
            self.__dev.output_on()

    def __get_volt(self):
        return self.__dev.volt

    def __set_volt(self, v):
        self.__dev.apply_volt = v

    volt = property(__get_volt, __set_volt)


source = Spannungsquelle(NTP6531.NTP6531(VCOMport))
source.volt = 12
print(source.volt)
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
