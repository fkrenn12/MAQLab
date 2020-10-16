import time
import paho.mqtt.client as mqtt
import os
import threading
import datetime

path = "/home/maqlab"


def mqtt_loop(_client):
    _client.loop_forever()


def on_connect(_client, userdata, flags, rc):
    # print("CONNACK received with code %d." % (rc))
    client.subscribe("maqlab/cmd/file/get/#", qos=0)
    client.subscribe("maqlab/cmd/file/store/#", qos=0)
    pass


def on_subscribe(_client, userdata, mid, granted_qos):
    pass
    # print("Subscribed: "+str(mid)+" "+str(granted_qos))


def on_message(_client, userdata, msg):
    # print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    try:
        # check topic
        if isinstance(msg.topic, bytes):
            topic = msg.topic.decode("utf-8")
        elif isinstance(msg.topic, str):
            topic = msg.topic
        else:
            return
        # check payload
        if isinstance(msg.payload, bytes):
            payload = msg.payload.decode("utf-8")
        elif isinstance(msg.payload, str):
            payload = msg.payload
        else:
            return

        if "/cmd/file/get" in topic:
            if not payload.startswith("/"):
                payload = "/" + payload
            filepath = path + payload
            print(filepath)
            if os.path.exists(filepath):
                try:
                    with open(filepath, mode='rb') as fp:
                        f = fp.read()
                        byte_array = bytes(f)
                        topic = topic.replace("/cmd/file/get", "/rep/file")
                        client.publish(topic + payload, byte_array, 0)
                except:
                    topic = topic.replace("/cmd/file/get", "/rep/file/err")
                    client.publish(topic, "internal error occurred")
            else:
                topic = topic.replace("/cmd/file/get", "/rep/file/err")
                client.publish(topic, "file does not exist")
        else:
            return
    except:
        pass


client = mqtt.Client()
client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message
client.username_pw_set("maqlab", "maqlab")
client.connect("techfit.at", 1883)

thread_mqttloop = threading.Thread(target=mqtt_loop, args=(client,))
thread_mqttloop.start()

time.sleep(1)
# -------------------------------------------------------------------------------
#                           M A I N - L O O P
# -------------------------------------------------------------------------------
while True:
    try:
        # nothing to do in the main looop
        time.sleep(10)
    except Exception:
        break
