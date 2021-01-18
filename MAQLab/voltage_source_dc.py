import MAQLab
from MAQLab import MqttMsg as msg
from MAQLab.instrument import instrument


class Foo(float):
    def __new__(cls, value, extra):
        return float.__new__(cls)

    def __init__(self, value, extra):
        float.__init__(value)
        self.extra = extra


class SupplyVDC(float):
    def __init__(self, access=0):
        super().__init__()
        self.__accessnumber = access
        try:
            self.__command = "vdc"
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
