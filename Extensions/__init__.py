import threading
import datetime
import time
import shared as s


class Execute_command(threading.Thread):
    def __init__(self, sleep_interval=1):
        super().__init__()
        self.__lock = threading.Lock()
        self.__executing = False
        self._kill = threading.Event()
        self._executing = threading.Event()
        self.interval = sleep_interval
        self.function = None
        self.repetitions = 1
        self.interval = 1
        self.data = None
        self.__exe_counter = 0

    def run(self):

        while True:
            time.sleep(0.01)
            executing = False
            with self.__lock:
                executing = self.__executing
            if executing:
                # print("Do Something")
                # print(self.data["function"])
                # x = self.data["function"]
                # print(eval(x))

                # if hasattr(self.data["functions"], '__call__'):
                #    print(self.data["functions"]())
                #else:
                #    print(self.data["functions"])
                handler = self.data["handler"]
                if hasattr(handler, '__call__'):
                    handler(self.data["command"], self.data["payload"])
                    # handler("vdc?", 0)
                self.__exe_counter += 1
            else:
                pass

            is_killed = self._kill.wait(self.data["interval"])
            if is_killed:
                break

            if self.__exe_counter >= self.data["repetitions"]:
                self.executing = False


        print("Killing Thread")

    def kill(self):
        self._kill.set()

    def __get_executing(self):
        with self.__lock:
            value = self.__executing
        return value

    def __set_executing(self, value):
        with self.__lock:
            self.__executing = value
            self.__exe_counter = 0

    executing = property(__get_executing, __set_executing)


class Device(threading.Thread):
    def __init__(self):
        super().__init__()
        self.__comport = ""
        self.__invent_number = "0"
        self.commands = []
        self.sp = None
        self.mqtt = None

    # --------------------------------------------------------
    #  CREATED
    # --------------------------------------------------------
    def on_created(self, port, invent_number, sp):
        self.__comport = str(port)
        self.__invent_number = invent_number
        self.sp = sp  # subpub object
        print(str(datetime.datetime.now()) + "  :" + self.devicetype + " " + self.model + " plugged into "
              + self.__comport + ", Accessnumber is: " + str(invent_number))
        # subscribe to the internal subpub mqtt-broker
        # we use regular expressions
        # \A start (.+) beliebig und mindestens ein Zeichen (.+)$ beliebig und mindestens ein Zeichen und ein Ende
        # | bedeutet "oder" \? ist das Zeichen "?" weil ? in regex eine Bedeutung hat
        self.mqtt = sp.subscribe("(\A(.+)/cmd/" + self.__invent_number + "/(.+)$)|(\A(.+)cmd/\?$)")

    # --------------------------------------------------------
    #  READ FROM MQTT queue
    # --------------------------------------------------------
    def read_from_mqtt(self):
        try:
            match, data = self.mqtt.get(block=False)
            return match.string, data
            # self.validate(match.string, data)
        except:
            raise Exception

    # --------------------------------------------------------
    #  V A L I D A T E
    # --------------------------------------------------------
    def execute_standard_commands(self, topic, payload, t, p):
        try:
            # self.validate_topic(topic=topic)
            # self.validate_payload(payload=payload)
            reply = t["reply"]
            command = t["command"]
            if command == s.topic_access_number:
                self.sp.publish(reply, str(self.__invent_number))
                raise Exception

            if t["matching"]:
                # matching, we handle the standard commands
                if command == "?":
                    self.sp.publish(reply + "/manufactorer", self.manufactorer)
                    self.sp.publish(reply + "/devicetype", self.devicetype)
                    self.sp.publish(reply + "/model", self.model)
                    self.sp.publish(reply + "/serialnumber", str(self.serialnumber))
                    self.sp.publish(reply + "/commands", str(self.commands))
                    raise Exception
                elif command == "echo?" or reply == "ping?":
                    self.sp.publish(reply, str(datetime.datetime.utcnow()))
                    raise Exception
            else:
                # accessnumber is not matching
                return
        except:
            raise Exception

    # --------------------------------------------------------
    #  V A L I D A T E  incoming  T O P I C
    # --------------------------------------------------------
    def validate_topic(self, topic):
        matching = False
        try:
            topic = topic.decode("utf-8")
        except:
            pass

        try:
            topic = topic.lower()
            topic_splitted = topic.split("/")
        except:
            raise Exception

        split_count = len(topic_splitted)
        if 3 <= split_count < 7 and topic_splitted[0] == s.topic_root:
            try:
                index_of_cmd = topic_splitted.index(s.topic_cmd)
                reply_topic = topic.replace(s.topic_cmd, s.topic_reply)
                if topic_splitted[index_of_cmd + 1] == s.topic_request:
                    command = s.topic_access_number
                    reply_topic = reply_topic.replace(s.topic_request, "")
                    reply_topic = reply_topic + self.model + "/" + s.topic_access_number
                else:
                    command = topic_splitted[index_of_cmd + 2]
                    command = command.replace("1", "")
                    command = command.replace(" ", "")
                    if topic_splitted[index_of_cmd + 1] == str(self.__invent_number):
                        matching = True
                return {"topic": topic, "command": command, "reply": reply_topic, "matching": matching}
            except:
                raise Exception
        else:
            raise Exception

    # --------------------------------------------------------
    #  V A L I D A T E  incoming  P A Y L O A D
    # --------------------------------------------------------
    def validate_payload(self, payload):
        timestamp = str(datetime.datetime.utcnow())
        payload_error = s.payload_error + " " + timestamp
        payload_accepted = s.payload_accepted + " " + timestamp
        payload_limited = s.payload_limited + " " + timestamp
        payload_command_error = s.payload_command_error + " " + timestamp
        payload_float = 0
        payload_json = "{}"
        try:
            try:
                payload = payload.decode("utf-8")
            except:
                pass
            try:
                payload = payload.strip(" ")
                if not (str(payload).startswith("{") and str(payload).endswith("}")):
                    raise
                payload_json = payload
            except:
                # it is not json
                # print("NO JSON")
                if payload == "":
                    payload = "0"
                try:
                    payload_float = float(payload)
                except:
                    payload_float = 0.0

            return {"error": payload_error,
                    "accepted": payload_accepted,
                    "limited": payload_limited,
                    "command_error": payload_command_error,
                    "float": payload_float,
                    "json": payload_json}
        except:
            raise



    # --------------------------------------------------------
    #  DESTROYED
    # --------------------------------------------------------
    def on_destroyed(self):
        print(str(datetime.datetime.now()) + "  :" + self.model + " removed from " + self.__comport)
        self.__comport = ""

    def __get_accessnumber(self):
        return self.__invent_number

    accessnumber = property(__get_accessnumber)
