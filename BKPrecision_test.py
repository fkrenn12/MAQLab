import serial
import BKPrecision
import time

dev = BKPrecision.BK2831E("com30")

print(dev.devicetype)
print(dev.manufactorer)
print(dev.serialnumber)
print(dev.model)

#dev.set_mode_vdc_auto_range()
# dev.set_mode_frequency_auto_range()
while True:

    dev.set_mode_vdc_auto_range()
    #time.sleep(2)
    dev.measure()
    #print(dev.volt)

    dev.set_mode_idc_range_200mA()
    #time.sleep(2)
    dev.measure()
    print(dev.volt, dev.current)
