from Devices import Keithley_SM2400
import time

dev = Keithley_SM2400.SM2400("com3")

print(dev.devicetype)
print(dev.manufactorer)
print(dev.serialnumber)
print(dev.model)

'''
print(dev.getparameter())
print(dev.idstring)
print(dev.model)
print(dev.serialnumber)
print(dev.manufactorer)
print(dev.devicetype)
'''


print("Voltage source")
#dev.set_mode_voltage_source(20, 0.5)
#dev.disable_human_security_mode()
dev.set_mode_voltage_source(30,1)
#dev.volt = 1
#dev.measure()
#dev.set_output_on()
#dev.measure()
#print(dev.volt, dev.current)
#print(dev.volt)

for i in range(1, 20000):
    dev.volt = i
    time.sleep(0.5)
    dev.measure()
    print(dev.current_as_string, dev.volt_as_string)
    time.sleep(0.1)


'''
dev.setOutput_off()
'''

'''
print("Current source")
dev.disable_human_security_mode()
dev.set_mode_current_source(0.5, 200)
time.sleep(1)
dev.current = 0.05

for i in range(10, 1000):
    #dev.current = i / 400
    #dev.volt = i/10
    dev.measure()
    print(dev.volt, dev.current)
    time.sleep(1)
'''

'''
print("Voltmeter")
dev.set_mode_voltmeter()
for i in range(1, 10):
    dev.measure()
    print(dev.volt)
    time.sleep(1)

print("Amperemeter")
dev.set_mode_amperemeter()
for i in range(1, 10):
    dev.measure()
    print(dev.current)
    time.sleep(1)
'''
'''
print("Sink Mode")
dev.set_mode_sink(0)
time.sleep(5)
for i in range(10, 1000):
    dev.current = i / 100
    print(dev.volt, dev.current)
    time.sleep(0.05)

time.sleep(1)
'''

'''
print("ohmmeter")
dev.set_mode_ohmmeter_4wire()
for i in range (0, 2000):
    #print(dev.getValue())
    #dev.setSinkCurrent(i/10)
    dev.measure()
    print(dev.volt, dev.current, dev.resistance)
    time.sleep(0.1)

#dev.setModeSink(0)
dev.set_output_off()
time.sleep(5)
# dev.setOutput_off()
'''

