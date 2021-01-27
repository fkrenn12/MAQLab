import time
import paho.mqtt.client as paho
import datetime
import queue
import threading
import secrets

mqtt_hostname = "mqtt.techfit.at"
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
class Mqtt:

    def __init__(self, host, port, user, password, session_id):
        try:
            self.__q_out = queue.Queue()
            print(str(datetime.datetime.now()) + "  :" + "MQTT - started")
            self.__mqtt_hostname = str(host)
            self.__mqtt_port = int(port)
            self.__mqtt_user = str(user)
            self.__mqtt_pass = str(password)
            self.__session_id = session_id
            self.__lock = threading.Lock()
            self.__client = paho.Client()
            self.__client.on_connect = self.__on_connect
            self.__client.on_disconnect = self.__on_disconnect
            self.__client.on_message = self.__on_message
            self.__client.reconnect_delay_set(min_delay=1, max_delay=5)
            self.__client.username_pw_set(self.__mqtt_user, self.__mqtt_pass)
            self.__client.connect(self.__mqtt_hostname, self.__mqtt_port)
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
    def __send(self, msg, stamp=""):
        try:
            self.__flush()
            # if it is existing remove the trailing /
            if str(msg.topic).startswith("/"):
                msg.topic = msg.topic[1:]
            self.__client.publish("maqlab/" + self.__session_id + "/" + stamp + "/cmd/" + msg.topic, msg.payload)
        except:
            raise MAQLabError("Send error")

    # ------------------------------------------------------------------------------
    #  Send a message ( public )
    # ------------------------------------------------------------------------------
    def send(self, msg):
        with self.__lock:
            try:
                self.__send(msg)
            except Exception as e:
                raise e

    # ------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------
    def __receive(self, block=True, timeout=1.0, stamp=""):
        try:
            rec_msg = self.__q_out.get(block=block, timeout=timeout)
            try:
                rec_msg = rec_msg.decode("utf-8")
            except:
                pass

            try:
                msg = MqttMsg(topic=rec_msg.split("|")[0], payload=rec_msg.split("|")[1])
                if stamp in msg.topic:
                    return msg
                else:
                    raise MAQLabError("Wrong message stamp - message discarded ")
            except:
                raise
        except:
            # return MQTT.Msg("ERROR", "TIMEOUT")
            raise MAQLabError("Timeout error")

    # ------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------
    # def receive(self, block=True, timeout=1.0):
    #     with self.__lock:
    #         try:
    #             return self.__receive(block, timeout)
    #        except Exception as e:
    #            raise e

    # ------------------------------------------------------------------------------
    # Send a message and wait for the answer
    # ------------------------------------------------------------------------------
    def send_and_receive(self, msg=None, block=True, timeout=1.0):
        with self.__lock:
            try:
                stamp = str(int((time.time() * 1000) % 1000000))
                self.__flush()
                self.__send(msg=msg, stamp=stamp)
                return self.__receive(block=block, timeout=timeout, stamp=stamp)
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
                stamp = str(int((time.time() * 1000) % 1000000))
                self.__flush()
                self.__send(msg=msg, stamp=stamp)
                while True:
                    try:
                        msg_received = self.__q_out.get(block=block, timeout=_timeout)
                        msg = MqttMsg(topic=msg_received.split("|")[0], payload=msg_received.split("|")[1])
                        if stamp in msg.topic:
                            # print(msg_received)
                            _timeout = burst_timout
                            msg_list.append(msg)
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
        try:
            detected_devices_raw = self.send_and_receive_burst(MqttMsg(topic="/?"), burst_timout=0.5)
            try:
                detected_devices = []
                for item in detected_devices_raw:
                    try:
                        if "accessnumber" in item.topic:
                            topic_splitted = item.topic.split("/")
                            devicename = topic_splitted[topic_splitted.index("rep") + 1]
                            accessnumber = int(item.payload)
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

    # ------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------
    def close(self):
        try:
            self.__client.on_disconnect = None
            self.__client.on_connect = None
            self.__client.disconnect()
        except:
            pass

    def __get_hostname(self):
        return self.__mqtt_hostname

    def __get_port(self):
        return self.__mqtt_port

    def __get_user(self):
        return self.__mqtt_user

    def __get_password(self):
        return self.__mqtt_pass

    # ------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------
    def __str__(self):
        return self.__session_id

    hostname = property(__get_hostname)
    port = property(__get_port)
    user = property(__get_user)
    password = property(__get_password)


try:
    mqtt = Mqtt(host=mqtt_hostname,
                port=mqtt_port,
                user=mqtt_user,
                password=mqtt_pass,
                session_id=secrets.token_urlsafe(3).lower())
except Exception as e:
    mqtt = None
    print(e)
