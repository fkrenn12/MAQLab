from Devices.BKPrecision import E2831

dev = E2831.BK2831E("com4")

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
