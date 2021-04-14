import threading
import datetime
import shared as s
import External_modules.subpub as subpub

class Device(threading.Thread):
    def __init__(self):
        super().__init__()
        self.__comport = ""
        self.__invent_number = "0"
        self.sp = None
    # --------------------------------------------------------
    #  V A L I D A T E  incoming  T O P I C
    # --------------------------------------------------------
    def validate_topic(self, topic, serial_number, model):
        command = ""
        matching = False
        reply_topic = ""
        try:
            topic = topic.decode("utf-8")
        except:
            pass

        try:
            topic = topic.lower()
            topic_splitted = topic.split("/")
        except:
            raise

        split_count = len(topic_splitted)
        if 3 <= split_count < 7 and topic_splitted[0] == s.topic_root:
            try:
                index_of_cmd = topic_splitted.index(s.topic_cmd)
                reply_topic = topic.replace(s.topic_cmd, s.topic_reply)
                if topic_splitted[index_of_cmd + 1] == s.topic_request:
                    command = s.topic_access_number
                    reply_topic = reply_topic.replace(s.topic_request, "")
                    reply_topic = reply_topic + model + "/" + s.topic_access_number
                else:
                    command = topic_splitted[index_of_cmd + 2]
                    command = command.replace("1", "")
                    command = command.replace(" ", "")
                    if topic_splitted[index_of_cmd + 1] == str(serial_number):
                        matching = True
                return {"topic": topic, 'cmd': command, 'matching': matching, 'reply': reply_topic}
            except:
                raise
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
            # try:
            #    dummy = payload.lower()
            # except:
            #    raise
            # print(payload)
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
                    # payload_float = payload.replace('off', "0")
                    # payload_float = payload.replace("on", "1")
                    payload_float = float(payload)
                except:
                    payload_float = 0j
        except:
            raise

        return {'payload': payload,
                'payload_float': payload_float,
                'payload_json': payload_json,
                'payload_error': payload_error,
                'payload_accepted': payload_accepted,
                'payload_command_error': payload_command_error,
                'payload_limited': payload_limited}

    def on_created(self, port, invent_number, sp):
        self.__comport = str(port)
        self.__invent_number = invent_number
        self.sp = sp
        print(str(datetime.datetime.now()) + "  :" + self.devicetype + " " + self.model + " HOHO plugged into " + self.__comport + ", Accessnumber is: "
              + str(invent_number))

        self.mqtt = sp.subscribe("(\A(.+)/cmd/" + self.__invent_number + "/(.+)$)|(\A(.+)cmd/\?$)")

    def on_destroyed(self):
        print(str(datetime.datetime.now()) + "  :" + self.model + " removed from " + self.__comport)
        self.__comport = ""

    def __get_accessnumber(self):
        return self.__invent_number

    accessnumber = property(__get_accessnumber)

