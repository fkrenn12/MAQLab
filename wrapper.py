import MAQLab
import time
import datetime


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
        m.topic = "cmd/9040/vdc"
        m.payload = str(volt / 2.0)
        rec = MAQLab.mqtt.send_and_receive(m)
        print(rec.topic, rec.payload)

        time.sleep(1)
        while True:

            m.topic = "cmd/9040/vdc?"
            try:
                rec = MAQLab.mqtt.send_and_receive(m, timeout=2)
                # print(str(datetime.datetime.now()) + ":" + str(rec.topic), str(rec.payload))
            except:
                print(str(datetime.datetime.now()) + ": NTP-6531 NO RESPONSE")

            m.topic = "cmd/1287/vdc?"
            try:
                rec = MAQLab.mqtt.send_and_receive(m)
                # print(str(datetime.datetime.now()) + ":" + str(rec.topic), str(rec.payload))
            except:
                print(str(datetime.datetime.now()) + ": DELTA NO RESPONSE")

        m.topic = "cmd/9040/idc?"
        rec = MAQLab.mqtt.send_and_receive(m)
        print(rec.topic, rec.payload)

