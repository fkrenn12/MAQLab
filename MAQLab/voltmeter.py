import time
from MAQLab.instrument import instrument
import MAQLab

class msg:
    topic = "cmd/?"
    payload = ""

class Voltmeter(instrument):

    def __init__(self, access=0, type="DC", mode="single", phase=1):
        super().__init__(access)
        self.__accessnumber = access
        self.__type  = type
        self.__mode  = mode
        self.__phase = phase
        try:
            self.__command = "v" + type.lower() + str(phase) + "?"
        except:
            raise

    def __str__(self):

        msg.topic = "cmd/" + str(self.__accessnumber) + "/" + self.__command
        msg.payload = ""
        try:
            rep = MAQLab.mqtt.send_and_receive(msg, timeout=1)
        except:
            raise
        return str(rep.payload)

    def __float__(self):
        return 0.23




