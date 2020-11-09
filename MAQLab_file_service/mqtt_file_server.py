import time
import paho.mqtt.client as mqtt
import os
import threading
import datetime
# TODO: RECONNECTING !!!!!
# this is the path on the linux (debian 10) system
home_dir = "/home/maqlab"
host = "techfit.at"
port = 1883
username = "maqlab"
password = "maqlab"


# -------------------------------------------------------------
#   M Q T T - callback functions
# -------------------------------------------------------------
def mqtt_loop(_client):
    while True:
        time.sleep(0.05)
        _client.loop()


def on_connect(_client, userdata, flags, rc):
    if rc == 0:
        client.subscribe("maqlab/+/cmd/file/get/#", qos=0)
        client.subscribe("maqlab/+/cmd/file/store/#", qos=0)
    pass


def on_message(_client, userdata, msg):
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
            filepath = home_dir + payload
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
client.on_message = on_message
client.username_pw_set(username, password)
client.connect(host, port)

thread_mqttloop = threading.Thread(target=mqtt_loop, args=(client,))
thread_mqttloop.start()

# -------------------------------------------------------------------------------
#                           M A I N - L O O P
# -------------------------------------------------------------------------------
while True:
    try:
        # yeaaa, there is nothing to do in the main loop
        time.sleep(10)
    except Exception:
        break
