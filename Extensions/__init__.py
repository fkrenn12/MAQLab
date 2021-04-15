import threading
import datetime
import shared as s


class Device(threading.Thread):
    def __init__(self):
        super().__init__()
        self.__comport = ""
        self.__invent_number = "0"
        self.commands = []
        self.sp = None
        self.mqtt = None
        self.matching = False
        self.topic = ""
        self.topic_reply = ""
        self.topic_cmd = ""
        self.payload_error = ""
        self.payload_accepted = ""
        self.payload_limited = ""
        self.payload_command_error = ""
        self.payload_float = 0
        self.payload_json = "{}"

    # --------------------------------------------------------
    #  V A L I D A T E
    # --------------------------------------------------------
    def validate(self, topic, payload):
        try:
            self.validate_topic(topic=topic)
            self.validate_payload(payload=payload)
            if self.topic_cmd == s.topic_access_number:
                self.sp.publish(self.topic_reply, str(self.__invent_number))
                raise Exception
            elif not self.matching:
                raise Exception
            # matching, so and we handle the standard commands
            if self.topic_cmd == "?":
                self.sp.publish(self.topic_reply + "/manufactorer", self.manufactorer)
                self.sp.publish(self.topic_reply + "/devicetype", self.devicetype)
                self.sp.publish(self.topic_reply + "/model", self.model)
                self.sp.publish(self.topic_reply + "/serialnumber", str(self.serialnumber))
                self.sp.publish(self.topic_reply + "/commands", str(self.commands))
                raise Exception
            elif self.topic_cmd == "echo?" or self.topic_cmd == "ping?":
                self.sp.publish(self.topic_reply, str(datetime.datetime.utcnow()))
                raise Exception
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
                self.topic = topic
                self.topic_cmd = command
                self.topic_reply = reply_topic
                self.matching = matching
            except:
                raise Exception
        else:
            raise Exception

    # --------------------------------------------------------
    #  V A L I D A T E  incoming  P A Y L O A D
    # --------------------------------------------------------
    def validate_payload(self, payload):
        timestamp = str(datetime.datetime.utcnow())
        self.payload_error = s.payload_error + " " + timestamp
        self.payload_accepted = s.payload_accepted + " " + timestamp
        self.payload_limited = s.payload_limited + " " + timestamp
        self.payload_command_error = s.payload_command_error + " " + timestamp
        self.payload_float = 0
        self.payload_json = "{}"
        try:
            try:
                payload = payload.decode("utf-8")
            except:
                pass
            try:
                payload = payload.strip(" ")
                if not (str(payload).startswith("{") and str(payload).endswith("}")):
                    raise
                self.payload_json = payload
            except:
                # it is not json
                # print("NO JSON")
                if payload == "":
                    payload = "0"
                try:
                    self.payload_float = float(payload)
                except:
                    self.payload_float = 0.0
        except:
            raise

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
    #  DESTROYED
    # --------------------------------------------------------
    def on_destroyed(self):
        print(str(datetime.datetime.now()) + "  :" + self.model + " removed from " + self.__comport)
        self.__comport = ""

    def __get_accessnumber(self):
        return self.__invent_number

    accessnumber = property(__get_accessnumber)
