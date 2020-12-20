import MAQLab
import time


class msg:
    topic = "cmd/?"
    payload = "10"


print(MAQLab.mqtt)
print(MAQLab.mqtt.connected_devices())
m = msg()
# rec = MAQLab.mqtt.send_and_receive_burst(m, burst_timout=1)
# print(rec)

while True:
    msg.topic = "cmd/1287/vdc?"
    msg.payload = ""
    rec = MAQLab.mqtt.send_and_receive(m)
    print(rec.topic, rec.payload)

    for volt in range(0, 8):
        print("Set to: " + str(volt / 2.0))
        msg.topic = "cmd/9574/vdc"
        msg.payload = str(volt / 2.0)
        rec = MAQLab.mqtt.send_and_receive(m)
        print(rec.topic, rec.payload)

        time.sleep(4)
        msg.topic = "cmd/9574/vdc?"
        rec = MAQLab.mqtt.send_and_receive(m)
        print(rec.topic, rec.payload)
        msg.topic = "cmd/9574/idc?"
        rec = MAQLab.mqtt.send_and_receive(m)
        print(rec.topic, rec.payload)

print(float(MAQLab.mqtt))
print(int(MAQLab.mqtt))
print(str(MAQLab.mqtt))
