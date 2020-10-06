# --------------------------------------------------------
from Devices.BKPrecision import E2831


# --------------------------------------------------------
class BK2831E(E2831.BK2831E):
    def __init__(self, _port, _baudrate=9600):
        super().__init__(_port, _baudrate)

    @staticmethod
    def mqttmessage(_msg):
        pass
        # print("NEW BK2831E:" + _msg.topic + " " + str(_msg.qos) + " " + str(_msg.payload))
        print(_msg.topic, _msg.payload)

    def on_created(self):
        print("BK2831E Ser:" + str(self.serialnumber) + " found")

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
        except:
            print("ERR publish")

        pass
