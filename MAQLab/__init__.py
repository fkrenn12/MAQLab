import time
import paho.mqtt.client as paho
import datetime
import queue
import threading
import secrets

mqtt_hostname = "techfit.at"
mqtt_port = 1883
mqtt_user = "maqlab"
mqtt_pass = "maqlab"


class MqttMsg:
    def __init__(self, topic, payload=""):
        self.topic = topic
        self.payload = payload


class MAQLabError(Exception):
    pass


# --------------------------------------------------------------------------------
# Class                             M Q T T
# --------------------------------------------------------------------------------
class MQTT:
    class Msg:
        def __init__(self, topic, payload=""):
            self.topic = topic
            self.payload = payload

    def __init__(self, host, port, user, password, session_id):
        try:
            self.__q_out = queue.Queue()
            print(str(datetime.datetime.now()) + "  :" + "MQTT - started")
            self.__session_id = session_id
            self.__lock = threading.Lock()
            self.__client = paho.Client()
            self.__client.on_connect = self.__on_connect
            self.__client.on_disconnect = self.__on_disconnect
            self.__client.on_message = self.__on_message
            self.__client.reconnect_delay_set(min_delay=1, max_delay=5)
            self.__client.username_pw_set(user, password)
            self.__client.connect(host, port)
            self.__client.loop_start()
            attemptions = 1
            while not self.__client.is_connected():
                print(str(datetime.datetime.now()) + "  :MQTT - connecting...attempt#" + str(attemptions))
                time.sleep(1)
                attemptions += 1

            print(str(datetime.datetime.now()) + "  :" + "MQTT - ready")
        except Exception as e:
            print(e)
            print(
                str(datetime.datetime.now()) + "  :" + "MAQlab - Connection Error! Are you connected to the internet?")
            raise e

    # --------------------------------------------------------
    # MQTT Broker callback on_connect
    # --------------------------------------------------------
    def __on_connect(self, _client, userdata, flags, rc):
        if rc == 0:
            print(str(datetime.datetime.now()) + "  :" + "MQTT - connected.")
            self.__client.subscribe("maqlab/" + str(self.__session_id) + "/rep/#", qos=0)
            self.__client.subscribe("maqlab/" + str(self.__session_id) + "/+/rep/#", qos=0)
            print(str(datetime.datetime.now()) + "  :" + "MQTT - Subscriptions done.")

    # ------------------------------------------------------------------------------
    # MQTT Broker callback on_disconnect
    # ------------------------------------------------------------------------------
    def __on_disconnect(self, _client, userdata, rc):
        if rc != 0:
            print(str(datetime.datetime.now()) + "  :" + "Unexpected MQTT-Broker disconnection.")

    # ------------------------------------------------------------------------------
    # MQTT Broker callback on_message
    # ------------------------------------------------------------------------------
    def __on_message(self, _client, _userdata, _msg):
        # check topic
        try:
            topic = _msg.topic.decode("utf-8")
        except:
            try:
                topic = _msg.topic.replace(" ", " ")
            except:
                return
        # check payload
        try:
            payload = _msg.payload.decode("utf-8")
        except:
            try:
                payload = _msg.payload.replace(" ", " ")
            except:
                return

        # print(_msg.topic, _msg.payload)
        # on_message is called from an other thread and therefore
        # the object _msg could be manipulated immediately
        # after putting it on the queue before it is handled
        # from the following stage.
        # The solution is to send topic and payload as string rather than as object
        self.__q_out.put(topic + "|" + payload, block=False, timeout=0)

    # ------------------------------------------------------------------------------
    #  Flush the queue
    # ------------------------------------------------------------------------------
    def __flush(self, block=False, timeout=0):
        while True:
            try:
                if self.__q_out.empty():
                    return
                else:
                    self.__q_out.get(block=block, timeout=timeout)
            except:
                return

    # ------------------------------------------------------------------------------
    #  Send internal use
    # ------------------------------------------------------------------------------
    def __send(self, msg):
        try:
            self.__flush()
            # if it is existing remove the trailing /
            if str(msg.topic).startswith("/"):
                msg.topic = msg.topic[1:]
            self.__client.publish("maqlab/" + self.__session_id + "/cmd/" + msg.topic, msg.payload)
        except:
            raise MAQLabError("Send error")

    # ------------------------------------------------------------------------------
    #  Send a message ( public )
    # ------------------------------------------------------------------------------
    def send(self, msg):
        with self.__lock:
            try:
                self.send(msg)
            except Exception as e:
                raise e

    # ------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------
    def __receive(self, block=True, timeout=1.0):
        try:
            rec_msg = self.__q_out.get(block=block, timeout=timeout)
            if isinstance(rec_msg, bytes):
                rec_msg = rec_msg.decode("utf-8")
            if isinstance(rec_msg, str):
                msg = MQTT.Msg(topic=rec_msg.split("|")[0], payload=rec_msg.split("|")[1])
                return msg
            else:
                raise
        except:
            # return MQTT.Msg("ERROR", "TIMEOUT")
            raise MAQLabError("Timeout error")

    # ------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------
    def receive(self, block=True, timeout=1.0):
        with self.__lock:
            try:
                return self.__receive(block, timeout)
            except Exception as e:
                raise e

    # ------------------------------------------------------------------------------
    # Send a message and wait for the answer
    # ------------------------------------------------------------------------------
    def send_and_receive(self, msg, block=True, timeout=1.0):
        with self.__lock:
            try:
                self.__flush()
                self.__send(msg)
                return self.__receive(block, timeout)
            except Exception as e:
                raise e

    # ------------------------------------------------------------------------------
    # Send a message and returns a list of all answers
    # ------------------------------------------------------------------------------
    def send_and_receive_burst(self, msg, block=True, timeout=1.0, burst_timout=1.0):
        _timeout = timeout
        msg_list = list()
        with self.__lock:
            try:
                self.__send(msg)
                while True:
                    try:
                        msg_received = self.__q_out.get(block=block, timeout=_timeout)
                        # print(msg_received)
                        _timeout = burst_timout
                        msg_list.append(msg_received)
                    except:
                        if len(msg_list) == 0:
                            raise MAQLabError("Empty data")
                        return msg_list
            except Exception as e:
                raise e

    # ------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------
    def __load_connected_devices(self):
        msg = MQTT.Msg(topic="/?")
        try:
            detected_devices_raw = self.send_and_receive_burst(msg, burst_timout=0.5)
            try:
                detected_devices = []
                for item in detected_devices_raw:
                    try:
                        items = item.split("|")[0].split("/")
                        i = list(items).index("rep")
                        devicename = items[i + 1]
                        accessnumber = int(item.split("|")[1])
                        detected_devices.append(tuple((devicename, accessnumber)))
                    except:
                        raise
            except:
                raise
        except:
            raise
        return detected_devices

    # ------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------
    def available_devices(self):
        try:
            return self.__load_connected_devices()
        except:
            raise MAQLabError("MAQLab could not load the list of available devices")

    def __str__(self):
        return self.__session_id


mqtt = MQTT(host=mqtt_hostname,
            port=mqtt_port,
            user=mqtt_user,
            password=mqtt_pass,
            session_id=secrets.token_urlsafe(3).lower())
