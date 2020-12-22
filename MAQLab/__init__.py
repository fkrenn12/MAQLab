import time
import paho.mqtt.client as paho
import datetime
import queue
import threading


class MAQLabError(Exception):
    pass


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

            self.__load_connected_devices()
            '''
            self.__msg = MQTT.Msg(topic="cmd/?")
            try:
                self.__detected_devices = self.send_and_receive_burst(self.__msg, burst_timout=0.5)
            except Exception as e:
                print(e)
                print("Could not receive the list of detected devices")
                raise e
            '''
            print(str(datetime.datetime.now()) + "  :" + "MQTT - ready")
        except Exception as e:
            print(e)
            print(
                str(datetime.datetime.now()) + "  :" + "MAQlab - Connection Error! Are you connected to the internet?")

    # --------------------------------------------------------
    # MQTT Broker callbacks
    # --------------------------------------------------------
    def __on_connect(self, _client, userdata, flags, rc):
        if rc == 0:
            print(str(datetime.datetime.now()) + "  :" + "MQTT - connected.")
            self.__client.subscribe("maqlab/" + str(self.__session_id) + "/rep/#", qos=0)
            # client.subscribe("maqlab/#")

    # ------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------
    def __on_disconnect(self, _client, userdata, rc):
        if rc != 0:
            print(str(datetime.datetime.now()) + "  :" + "Unexpected MQTT-Broker disconnection.")

    # ------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------
    def __on_message(self, _client, _userdata, _msg):
        # check topic
        if isinstance(_msg.topic, bytes):
            topic = _msg.topic.decode("utf-8")
        elif isinstance(_msg.topic, str):
            topic = _msg.topic
        else:
            return
        if isinstance(_msg.payload, bytes):
            payload = _msg.payload.decode("utf-8")
        elif isinstance(_msg.payload, str):
            payload = _msg.payload
        else:
            return
        # print(_msg.topic, _msg.payload)
        # on_message is called from an other thread and therefore
        # the object _msg could be manipulated immediately
        # after putting it on the queue before it is handled
        # from the following stage.
        # The solution is to send topic and payload as string rather than
        # put it as object on the queue.
        self.__q_out.put(topic + "|" + payload, block=False, timeout=0)

    # ------------------------------------------------------------------------------
    #
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
    #
    # ------------------------------------------------------------------------------
    def __send(self, msg):
        try:
            self.__flush()
            self.__client.publish("maqlab/" + self.__session_id + "/" + msg.topic, msg.payload)
        except:
            raise MAQLabError("Send error")

    # ------------------------------------------------------------------------------
    #
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
                rec_msg_splitted = rec_msg.split("|")
                msg = MQTT.Msg(topic=rec_msg_splitted[0], payload=rec_msg_splitted[1])
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
    #
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
    #
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
    def all(self):
        print("Ja das sind die Geräte1")
        print("Ja das sind die Geräte2")

    # ------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------
    def __load_connected_devices(self):
        msg = MQTT.Msg(topic="cmd/?")
        try:
            self.__detected_devices = self.send_and_receive_burst(msg, burst_timout=0.5)
        except:
            pass

    # ------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------
    def connected_devices(self):
        with self.__lock:
            try:
                return self.__detected_devices
            except:
                raise MAQLabError("MAQLab could not load the list of detected devices")

    def __str__(self):
        return self.__session_id


mqtt = MQTT(host="techfit.at", port=1883, user="maqlab", password="maqlab", session_id="s01")
