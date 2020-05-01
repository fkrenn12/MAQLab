import serial
import time
import Manson
# ---------------------------------------------------
# be sure to make proper COM port settings
# ---------------------------------------------------
VCOMport = "com4"  # -> change to your needs
NTP = Manson.NTP6531(VCOMport)

print(NTP.devicetype)
print(NTP.manufactorer)
print(NTP.serialnumber)
print(NTP.model)

NTP.volt_max = 20  # max spannung in V für die schaltung
NTP.current_max = 2  # max strom für die schaltung

NTP.current = 1.5  # strombegrenzung
NTP.output_on()

for i in range(10, 100):
    NTP.volt = i/10
    #print(NTP.volt)
    time.sleep(2)  # wait for voltage setting / 2sec is good
    print(NTP.current_display_as_string + "  " + NTP.volt_display_as_string)
NTP.output_off()
