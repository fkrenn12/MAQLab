# --------------------------------------------------------
from Devices import Manson_NTP6531, BKPrecision_2831E, Keithley_SM2400


class NTP6531(Manson_NTP6531.NTP6531):

    def __init__(self, _port, _baudrate=9600):
        super().__init__(_port, _baudrate)

    @staticmethod
    def mqttmessage(_msg):
        # print(_msg.topic)
        pass

    def on_created(self):
        print("NTP6531Ser:" + str(self.serialnumber) + " plugged in")

    def on_destroyed(self):
        print("NTP6531 removed")

    def execute(self):
        pass
