import time
import paho.mqtt.client as mqtt
import os
import threading
import datetime
import json

PING_TOPIC = "maqlab/ping/"
PING_INTERVAL_MS = 2000  # ping interval time in ms
MQTT_TIMEOUT_MS = 5000  # no response timeout in ms
# this is the path on the linux (debian 10) system
home_dir = "/home/maqlab"
host = "techfit.at"
port = 1883
username = "maqlab"
password = "maqlab"
last_message_receive = 0


# -------------------------------------------------------------
#   M Q T T - callback functions
# -------------------------------------------------------------
def on_connect(_client, userdata, flags, rc):
    global last_message_receive
    if rc == 0:
        last_message_receive = 0
        # print("Connected")
        client.subscribe("maqlab/cmd/file/get/#", qos=0)
        client.subscribe("maqlab/cmd/file/store/#", qos=0)
        client.subscribe("maqlab/+/cmd/file/get/#", qos=0)
        client.subscribe("maqlab/+/cmd/file/store/#", qos=0)
        client.subscribe("maqlab/ping/#", qos=0)
    pass


def on_message(_client, userdata, msg):
    global last_message_receive
    last_message_receive = int(time.time() * 1000)
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
            # print(filepath)
            if os.path.exists(filepath):
                try:
                    with open(filepath, mode='rb') as fp:
                        j = json.loads(fp.read())
                        bsjson = json.dumps(obj=j, separators=(',', ':')).encode("utf-8")
                        topic = topic.replace("/cmd/file/get", "/rep/file")
                        client.publish(topic + payload, bsjson, 0)
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

# -------------------------------------------------------------------------------
#                           M A I N - L O O P
# -------------------------------------------------------------------------------
while True:
    # first connection to mqtt broker
    try:
        client.connect(host=host, port=port, keepalive=5)
        last_message_receive = 0
    except:
        # print("Exception - not connected")
        continue

    # initialize timer_2sec
    timer_2sec = int(time.time() * 1000)

    while True:
        # print(int(time.time() * 1000) - last_message_receive)
        if int(time.time() * 1000) - timer_2sec >= PING_INTERVAL_MS:
            timer_2sec = int(time.time() * 1000)
            # print("2sec")
            if client.is_connected():
                # print("CONN")
                try:
                    payload = str(datetime.datetime.utcnow().timestamp())
                    client.publish(topic=PING_TOPIC, payload=payload, retain=False)
                    # print("Ping")
                except:
                    # print("DISCONNECT")
                    client.disconnect()
                    break

        if last_message_receive > 0 and int(time.time() * 1000) - last_message_receive > MQTT_TIMEOUT_MS:
            client.disconnect()
            break

        client.loop(0.05)
