# --------------------------------------------------------
from Devices import BKPrecision_2831E


# --------------------------------------------------------
class BK2831E(BKPrecision_2831E.BK2831E):
    def __init__(self, _port, _baudrate=9600):
        super().__init__(_port, _baudrate)

    @staticmethod
    def mqttmessage(_msg):
        pass
        # print("NEW BK2831E:" + _msg.topic + " " + str(_msg.qos) + " " + str(_msg.payload))

    def on_created(self):
        print("BK2831E Ser:" + str(self.serialnumber) + " plugged in")

    def on_destroyed(self):
        print("BK2831E removed")

    def execute(self):
        anumber = 0
        try:
            anumber = self.volt
            # print(anumber)
        except:
            print("ERR get")
            pass
        try:
            pass
            # client.publish("Krenn/BK/Volt",str(anumber))
            # client.publish("Krenn/BK/Volt", "{:.2f}".format(anumber))
        except:
            print("ERR publish")

        pass
