import time
from Instruments import Manson_NTP6531

# ---------------------------------------------------
# be sure to make proper COM port settings
# ---------------------------------------------------
VCOMport = "com4"  # -> change to your needs

NTP = Manson_NTP6531.NTP6531(VCOMport)

print(NTP.devicetype)
print(NTP.manufactorer)
print(NTP.serialnumber)
print(NTP.model)


NTP.set_voltage_limit(10)
NTP.set_current_limit(0.5)
NTP.apply_current = 1.1  # strombegrenzung
for i in range(1, 10):
    NTP.output(True)
    time.sleep(0.3)
    NTP.output(False)
    time.sleep(0.3)

NTP.output_on()

for i in range(20, 300, 5):
    NTP.apply_volt = i/10
    time.sleep(3)  # wait for voltage setting / 2sec is a good valu2
    print(str(NTP.apply_volt) + ":" + NTP.current_as_string + "  " + NTP.volt_as_string + " " + NTP.source_mode)

NTP.output_off()
