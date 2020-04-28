import paho.mqtt.client as mqtt
from sshtunnel import SSHTunnelForwarder
import threading
import datetime
import logging
import time


class Mqtt:
    def __init__(self, ssh_host, ssh_user, ssh_pass, mqtt_user, mqtt_pass, message_handler=None, log_enabled=True):
        self.__dummy = 0
        self.__log_enabled = log_enabled
        self.__message_handler = message_handler
        self.__lock = threading.Lock()
        self.__ssh_host = ssh_host
        self.__ssh_user = ssh_user
        self.__ssh_pass = ssh_pass
        self.__mqtt_user = mqtt_user
        self.__mqtt_pass = mqtt_pass
        self.__stop_request = False
        self.__connected_state = False

        try:
            self.__tunnel = SSHTunnelForwarder(ssh_address_or_host=self.__ssh_host,
                                               ssh_username=self.__ssh_user,
                                               ssh_password=self.__ssh_pass,
                                               remote_bind_address=('127.0.0.1', 1883)
                                               )
            self.__tunnel.start()

            self.__log("SSH: Creating tunnel successful!")
        except:
            self.__log("SSH: Creating tunnel failed!", "Error")
            raise

        try:
            self.__client = mqtt.Client()
            self.__client.on_connect = self.on_connect
            self.__client.on_disconnect = self.on_disconnect
            self.__client.on_message = self.on_message
            self.__client.username_pw_set(self.__mqtt_user, self.__mqtt_pass)
            self.__client.connect("127.0.0.1", self.__tunnel.local_bind_port)
            self.__thread_mqtt_loop = threading.Thread(target=self.__mqtt_loop, args=(self.__client,))
            self.__thread_mqtt_loop.start()
            self.__log("Client connected successful!")
        except:
            self.__log("Client connecting failed!", "Error")
            raise

        pass

    def __del__(self):
        try:
            self.__client.disconnect()
        except:
            pass
        time.sleep(0.1)
        pass

    def __mqtt_loop(self, client):
        # client.loop_forever()
        while not self.__stop_request:
            client.loop(.1)
        self.__dummy = 1
        client.disconnect()
        time.sleep(0.5)
        self.__tunnel.close()
        del self.__tunnel

    def on_connect(self, client, userdata, flags, rc):
        self.__log("Connected!")
        self.__connected_state = True
        client.subscribe("#", qos=0)
        self.__dummy = 1

    def on_disconnect(self, client, userdata, rc):
        self.__connected_state = False
        if rc != 0:
            self.__log("Unexpected disconnection.", "Error")
        self.__tunnel.stop()
        self.__tunnel.start()
        client.reconnect()

    def on_message(self, client, userdata, msg):
        with self.__lock:
            if self.__message_handler is not None:
                self.__message_handler(msg)
        pass

    def __log(self, log_text, level="Info"):
        if self.__log_enabled:
            print(str(datetime.datetime.now()) + " : MQTT: " + str(log_text))
            if "Info" in level:
                logging.info("MQTT: "+log_text)
            elif "Error" in level:
                logging.error("MQTT: " + log_text)

    def __get_lock(self):
        return self.__lock

    def __get_client(self):
        return self.__client

    def __get_stop(self):
        return self.__stop_request

    def __set_stop(self, stop):
        self.__stop_request = stop

    def set_stop(self, stop):
        self.__stop_request = stop

    def __get_connected_state(self):
        return self.__connected_state

    lock = property(__get_lock)
    client = property(__get_client)
    stop_request = property(__get_stop, __set_stop)
    connected = property(__get_connected_state)

