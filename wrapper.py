import MAQLab
from MAQLab import maqlab
import time
import datetime
from MAQLab.voltmeter import Voltmeter

Vx = Voltmeter(1287)
print(float(Vx))




access =  9757

class msg:
    topic = "cmd/?"
    payload = "10"


# print(maqlab)
# print(maqlab.available_devices())

m = msg()
m.topic = "cmd/1287/output"
m.payload = 1
#if "ACCEPT" in MAQLab.mqtt.send_and_receive(m).payload:
#    print("OUTPUT ON")

clrRed = "ffbbff"

while True:
    # m.topic = "cmd/1287/vdc?"
    # m.payload = ""
    # rec = MAQLab.mqtt.send_and_receive(m)
    # print(rec.topic, rec.payload)

    for volt in range(5, 8):
        print("Set to: " + str(volt / 2.0))
        m.topic = str(access) + "/vdc"
        m.payload = str(volt / 2.0)
        #rec = MAQLab.mqtt.send_and_receive(m)
        #print(rec.topic, rec.payload)

        rel1 = 0
        while True:
            maqlab.send_and_receive(receive=False, command="clear*", accessnumber=8704)
            time.sleep(0.5)
            maqlab.send_and_receive(receive=False, command="fill_hsv", value="ffc050", accessnumber=8704)
            #time.sleep(2)
            try:
                color = clrRed
                #maqlab.send_and_receive(receive=False, command="clear", value=0, accessnumber=8704, block=False)
                maqlab.send_and_receive(receive=False, command="fillpixel_hsv/1,2", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="fillpixel_hsv/4,2", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/8", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/11", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/14", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/16", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/22", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/25", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/29", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="fillpixel_hsv*/34,3", value=color, accessnumber=8704)

                time.sleep(1)
                color = "ffa0ff"
                # maqlab.send_and_receive(receive=False, command="clear", value=0, accessnumber=8704, block=False)
                maqlab.send_and_receive(receive=False, command="fillpixel_hsv/1,2", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="fillpixel_hsv/4,2", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/8", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/11", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/14", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/16", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/22", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/25", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/29", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="fillpixel_hsv*/34,3", value=color, accessnumber=8704)

                time.sleep(1)
                color = "ff80ff"
                # maqlab.send_and_receive(receive=False, command="clear", value=0, accessnumber=8704, block=False)
                maqlab.send_and_receive(receive=False, command="fillpixel_hsv/1,2", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="fillpixel_hsv/4,2", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/8", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/11", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/14", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/16", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/22", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/25", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="setpixel_hsv/29", value=color, accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="fillpixel_hsv*/34,3", value=color, accessnumber=8704)
                

            except:
                print(str(datetime.datetime.now()) + ": DISPLAY NO RESPONESE")
            time.sleep(1.5)

            #m.topic = "cmd/" + str(access) + "/vdc?"
            #try:
            #    rec = MAQLab.mqtt.send_and_receive(m, timeout=1)
            #    print(str(datetime.datetime.now()) + ":" + str(rec.topic), str(rec.payload))
            #except:
            #    print(str(datetime.datetime.now()) + ": NTP-6531 NO RESPONSE")

            #m.topic = "cmd/1287/vdc?"
            #try:
            #    rec = MAQLab.mqtt.send_and_receive(m)
            #    print(str(datetime.datetime.now()) + ":" + str(rec.topic), str(rec.payload))
            #except:
            #    print(str(datetime.datetime.now()) + ": DELTA NO RESPONSE")

            if rel1 == 1:
                rel1 = 0
            else:
                rel1 = 1
            '''    
            try:
                maqlab.send_and_receive(command="rel/4", value=rel1, accessnumber=8385)
            except:
                print(str(datetime.datetime.now()) + ": ESP32 R4 NO RESPONSE REL1")
            
            time.sleep(5)
            try:
                # maqlab.send_and_receive(receive=False, command="fillpixel_hsv/0,10", value="cfffff", accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="fill_hsv", value="ee50ff", accessnumber=8704)
            except Exception as e:
                print(e)
                print(str(datetime.datetime.now()) + ": DISPLAY NO RESPONESE")
            time.sleep(0.5)
            try:
                # maqlab.send_and_receive(receive=False, command="fillpixel_hsv/0,10", value="cfffff", accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="fill_hsv", value="77ffff", accessnumber=8704)
            except Exception as e:
                print(e)
                print(str(datetime.datetime.now()) + ": DISPLAY NO RESPONESE")
            
            time.sleep(0.5)
            try:
                # maqlab.send_and_receive(receive=False, command="fillpixel_hsv/0,10", value="cfffff", accessnumber=8704)
                maqlab.send_and_receive(receive=False, command="fill_hsv", value="22ff50", accessnumber=8704)
            except Exception as e:
                print(e)
                print(str(datetime.datetime.now()) + ": DISPLAY NO RESPONESE")
            '''
            try:
                maqlab.send_and_receive(receive=False, command="rel/1", value=rel1, accessnumber=8385)
            except:
                print(str(datetime.datetime.now()) + ": ESP32 R4 NO RESPONSE REL2")

            try:
                maqlab.send_and_receive(receive=False, command="rel/2", value=rel1, accessnumber=8385)
            except:
                print(str(datetime.datetime.now()) + ": ESP32 R4 NO RESPONSE REL3")

            try:
                maqlab.send_and_receive(receive=False, command="rel/3", value=rel1, accessnumber=8385)
            except:
                print(str(datetime.datetime.now()) + ": ESP32 R4 NO RESPONSE REL4")


        m.topic = str(access) + "/idc?"
        rec = maqlab.send_and_receive(m)
        print(rec.topic, rec.payload)

