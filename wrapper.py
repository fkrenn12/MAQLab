import MAQLab
import time
import datetime
from MAQLab.voltmeter import Voltmeter

Vx = Voltmeter(1287)
print(float(Vx))




access =  9757

class msg:
    topic = "cmd/?"
    payload = "10"


print(MAQLab.mqtt)
print(MAQLab.mqtt.connected_devices())

m = msg()
m.topic = "cmd/1287/output"
m.payload = 1
if "ACCEPT" in MAQLab.mqtt.send_and_receive(m).payload:
    print("OUTPUT ON")


while True:
    m.topic = "cmd/1287/vdc?"
    m.payload = ""
    rec = MAQLab.mqtt.send_and_receive(m)
    print(rec.topic, rec.payload)

    for volt in range(5, 8):
        print("Set to: " + str(volt / 2.0))
        m.topic = "cmd/" + str(access) + "/vdc"
        m.payload = str(volt / 2.0)
        rec = MAQLab.mqtt.send_and_receive(m)
        print(rec.topic, rec.payload)


        while True:
            time.sleep(0.5)
            m.topic = "cmd/" + str(access) + "/vdc?"
            try:
                rec = MAQLab.mqtt.send_and_receive(m, timeout=1)
                print(str(datetime.datetime.now()) + ":" + str(rec.topic), str(rec.payload))
            except:
                print(str(datetime.datetime.now()) + ": NTP-6531 NO RESPONSE")

            m.topic = "cmd/1287/vdc?"
            try:
                rec = MAQLab.mqtt.send_and_receive(m)
                print(str(datetime.datetime.now()) + ":" + str(rec.topic), str(rec.payload))
            except:
                print(str(datetime.datetime.now()) + ": DELTA NO RESPONSE")

        m.topic = "cmd/" + str(access) + "/idc?"
        rec = MAQLab.mqtt.send_and_receive(m)
        print(rec.topic, rec.payload)

