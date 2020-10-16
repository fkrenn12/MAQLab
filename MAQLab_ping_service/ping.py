import time
import paho.mqtt.client as mqtt
import threading
import datetime


def mqtt_loop(_client):
    _client.loop_forever()


def on_connect(_client, userdata, flags, rc):
    pass


def on_subscribe(_client, userdata, mid, granted_qos):
    pass


def on_message(_client, userdata, msg):
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
        time.sleep(2)
        topic = "maqlab/ping/"
        payload = str(datetime.datetime.utcnow().timestamp())
        # print(payload)
        client.publish(topic=topic, payload=payload, retain=False)
    except Exception:
        pass
