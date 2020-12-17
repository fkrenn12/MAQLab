import asyncio
import datetime
import paho.mqtt.client as paho
import Extensions
import secrets

client = paho.Client()
session_id = secrets.token_urlsafe(5)
session_id = "wrapper_01"

q = asyncio.Queue(10)
# --------------------------------------------------------
# MQTT Broker callbacks
# --------------------------------------------------------
def on_connect(_client, userdata, flags, rc):
    if rc == 0:
        print(str(datetime.datetime.now()) + "  :" + "Connected to MQTT-Broker.")
        _client.subscribe("maqlab/" + str(session_id) + "/rep/#", qos=0)


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
def on_disconnect(_client, userdata, rc):
    if rc != 0:
        print(str(datetime.datetime.now()) + "  :" + "Unexpected disconnection.")
    # server.stop()
    # server.start()
    _client.reconnect()


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
def on_message(_client, _userdata, _msg):
    # check topic
    if isinstance(_msg.topic, bytes):
        topic = _msg.topic.decode("utf-8")
    elif isinstance(_msg.topic, str):
        topic = _msg.topic
    else:
        return
    # print(_msg.payload)
    q.put_nowait(_msg)


async def mqttloop(_client):
    while True:
        if _client is not None:
            _client.loop(0.0001)
        await asyncio.sleep(0.05)


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
async def connector(event_config_readed):
    global client
    print(str(datetime.datetime.now()) + "  :" + "MAQlab - Wrapper started")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.username_pw_set("maqlab", "maqlab")
    client.connect("techfit.at", 1883)
    while not client.is_connected():
        await asyncio.sleep(0.05)
    client.publish("maqlab/"+str(session_id)+"/cmd/?")
    msg = await q.get()
    print(msg.payload)
    q.task_done()

    # print(str(datetime.datetime.now()) + "  :" + "Requesting configuration files...")


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
async def main():
    event_config_readed = asyncio.Event()
    # create tasks
    global client
    task1 = loop.create_task(mqttloop(client))
    task2 = loop.create_task(connector(event_config_readed))
    # await event_config_readed.wait()
    # wait until all tasks finished
    await asyncio.wait([task1])
    # but will never happen in real !!!


if __name__ == "__main__":
    # Declare event loop
    loop = asyncio.get_event_loop()
    # Run the code until completing all task
    loop.run_until_complete(main())
    # Close the loop
    loop.close()
