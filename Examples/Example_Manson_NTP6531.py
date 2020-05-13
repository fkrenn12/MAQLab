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

NTP.volt_max = 20  # max spannung in V für die schaltung
NTP.current_max = 2  # max strom für die schaltung

NTP.apply_current = 1.5  # strombegrenzung
NTP.output_on()

for i in range(0, 100, 5):
    NTP.apply_volt = i/10
    #print(NTP.volt)
    time.sleep(2)  # wait for voltage setting / 2sec is a good value
    print(NTP.current_as_string + "  " + NTP.volt_as_string)
NTP.output_off()
