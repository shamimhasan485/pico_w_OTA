import network
import wifi_Manager
import config_Manager
from umqtt.simple import MQTTClient
import time
from time import sleep     
from machine import Pin
import machine
import gc
import ujson
from phew import logging
import ubinascii
import os

resetTime = "12:59" # device will reset Exact This Time



def get_MacID():
    mac_Address = ubinascii.hexlify(network.WLAN().config('mac')).decode()
    print("Device Mac Address: " + mac_Address)
    return mac_Address

def get_DeviceID():
    device_ID = ubinascii.hexlify(machine.unique_id()).decode()
    print("Device Hardware ID: " + device_ID)
    return device_ID

def get_IpAddress(wlan_Obj):
    splited = str(wlan_Obj).split(" ")
    get_Ip = splited[3]
    ip = get_Ip.split(">")
    Ip_Address = ip[0]
    return Ip_Address

def get_ConnMode(wlan_Obj):
    splited = str(wlan_Obj).split(" ")
    get_Mode = splited[1]
    return get_Mode

def resetEvery(interval):
    oldMillis = 0
    nowMillis = int(time.time())
    if(nowMillis - oldMillis >= interval):
        oldMillis = nowMillis
        return True
    else:
        return False

start_Time = logging.datetime_string()
config_Manager.update_DataToJson("device_StartTime", str(start_Time)) # for update the Start Time in JSON File

uniqueID = get_DeviceID()
config_Manager.update_DataToJson("device_ID", uniqueID) #for saving the device_ID in JSON File

device_ID = config_Manager.get_DataFromJson("device_ID")
mqtt_server = config_Manager.get_DataFromJson("mqtt_Server") #'mqtt.rozcomapp.com' #'64.225.85.222'
firmware_Version = config_Manager.get_DataFromJson("firmware_Version")
door_1_GPIO = config_Manager.get_DataFromJson("door_1_GPIO")
door_2_GPIO = config_Manager.get_DataFromJson("door_2_GPIO")
wlan_Led = config_Manager.get_DataFromJson("wlan_Led")


topic_Open = str(device_ID) + '/open'
topic_Close = str(device_ID) + '/close'
topic_GetStatus = str(device_ID) + '/get_status'
topic_StatusResult = str(device_ID) + '/status_result'
topic_ResetDevice = str(device_ID) + '/reset_device'
topic_Ip_Result = 'pico/ip_result'
topic_Alive = 'keep_alive'
topic_CheckMqtt = str(device_ID) + '/check_mqtt'
all_Topic = '#'


door_1 = Pin(door_1_GPIO, Pin.OUT)
door_1_Status = "close"

door_2 = Pin(door_2_GPIO, Pin.OUT)
door_2_Status = "close"

wlan_Led = Pin(wlan_Led, Pin.OUT)

door_1.on()
door_2.on()
wlan_Led.off()


previousMillis = 0
currentMillis = 0    
interval = 3600

nowTime = 0
oldTime = 0
led_blink_Interval = 3

oldMillis = 0
nowMillis = 0
mqttCheck_PublishInterval = 1

check_Mqtt_oldMillis = 0
check_Mqtt_nowMillis = 0
check_Mqtt_Interval = 10

wifi_Status = False
mqtt_Status = False

try:
  import usocket as socket
except:
  import socket


wlan = wifi_Manager.get_connection()
print("WLan Connecting")
print(wlan)

mac_ID = get_MacID()
ip_Address = get_IpAddress(wlan)
conn_Mode = get_ConnMode(wlan)

logging.info("Getting Device Mac ID" + mac_ID)

config_Manager.update_DataToJson("mac_ID", str(mac_ID))
config_Manager.update_DataToJson("device_IP", str(ip_Address))
config_Manager.update_DataToJson("connection_Mode", str(conn_Mode))

if wlan is None:
    print("Could not initialize the network connection.")
    logging.error("Could not initialize the network connection.")
    machine.reset()
    while True:
        
        pass  
    
print(" Pico W Connected to Router with " + ip_Address)
logging.info("PicoW Connected to " + ip_Address)
wifi_Status = True

def reset_Device(payload):
    json_Payload = ujson.loads(payload)
    reset_Status = json_Payload["reset_status"]
    logging.info("Restarting Device")
    
    if reset_Status is True:
        try:
            logging.info("Device Restarted!")
            os.remove("wifi.dat")
            machine.reset()
        except:
            logging.error("Device Restarted failed!")
            print('Reset Error')

def check_Mqtt(payload):
    json_Payload = ujson.loads(payload)
    mqtt_State = json_Payload["mqtt_Status"]
    print(mqtt_State)
    
    #if not mqtt_State

def door_Controller(incoming_topic, payload):
    global door_1_Status
    global door_2_Status
    close_after = 0

    logging.info("Recieved Payload from Topic: " + incoming_topic)

    
    print("Payload Recieved From: " + incoming_topic)
    if (topic_Open == incoming_topic):
        try:
            json_Payload = ujson.loads(payload)
            gate_Id = json_Payload["gate_id"]
            close_after = json_Payload["close_after"]
            print(close_after)
            
            logging.info("Recieved Payload: " + json_Payload)
            
            
        except:
            pass
        
        print("Topic Open")
        if gate_Id is "GPIO14":
            print("Door 1 open")
            door_1_Status = "open"
            door_1.off() # While Enable 'Auto close After' Please Comment this line 
            
            
     
            ################### For Auto Closing Door 1 #################
            nowTime = time.time()
            while True:
                door_1.off()
                if((time.time() - nowTime) >= close_after):
                    if(close_after > 0):
                        door_1.on()
                        door_1_Status = "close"
                    print(time.time()-nowTime)
                    ack_Payload = ujson.dumps({
                        "gate_id":"GPIO14",
                        "status": door_1_Status
                        })
                    
                    print(ack_Payload)
                    client.publish(topic_StatusResult, ack_Payload)
                    break
            ############################################################## 
     
            
        elif gate_Id is "GPIO15":
            print("Door_2 open")
            door_2_Status = "open"
            door_2.off() # While Enable 'Auto close After' Please Comment this line
            
            
           
            ################### For Auto Closing Door 2 #################
            nowTime = time.time()
            while True:
                door_2.off()
                if((time.time() - nowTime) >= close_after):
                    if(close_after > 0):
                        door_2.on()
                        door_2_Status = "close"
                    print(time.time()-nowTime)
                    ack_Payload = ujson.dumps({
                        "gate_id":"GPIO15",
                        "status":door_2_Status
                        })
                    
                    #print(ack_Payload)
                    client.publish(topic_StatusResult, ack_Payload)
                    break
            ##############################################################    
         
            
    elif (topic_Close == incoming_topic):
        json_Payload = ujson.loads(payload)
        gate_Id = json_Payload["gate_id"]
        
        if gate_Id is "GPIO14":
            door_1_Status = "closed"
            door_1.on()
            
            print("Closing Door 1!")
            
            status_Payload = ujson.dumps({
                "gate_id":"GPIO14",
                "status":"closed"
                })
            
            #print(status_Payload)
            client.publish(topic_StatusResult, status_Payload)
            
            
        elif gate_Id is "GPIO15":
            door_2_Status = "closed"
            door_2.on()
            
            print("Closing Door 2!")
            
            status_Payload = ujson.dumps({
                "gate_id":"GPIO15",
                "status":"closed"
                })
            
            #print(status_Payload)
            client.publish(topic_StatusResult, status_Payload)
            
    elif (topic_GetStatus == incoming_topic):
        json_Payload = ujson.loads(payload)
        gate_Id = json_Payload["gate_id"]
        
        if gate_Id is "GPIO14":
            ## have to read from door sensor and publish the door status i think
            status_Payload = ujson.dumps({
                "gate_id":"GPIO14",
                "status":door_1_Status ## Read from sensor
                })
            
            print(status_Payload)
            client.publish(topic_StatusResult, status_Payload)
            
        if gate_Id is "GPIO15":
            ## have to read from door sensor and publish the door status i think
            status_Payload = ujson.dumps({
                "gate_id":"GPIO15",
                "status":door_2_Status ## Read from sensor
                })
            
            print(status_Payload)
            client.publish(topic_StatusResult, status_Payload)

    
def sub_cb(topic, payload):
    try:
        
        incoming_topic = topic.decode('utf-8')
        payload = payload.decode('utf-8')
        
        if incoming_topic == topic_CheckMqtt:
            mqtt_Status = True
        
        if incoming_topic == topic_ResetDevice:
            reset_Device(payload)
            
        else:
            door_Controller(incoming_topic, payload)
            
        print(incoming_topic)
        
    except OSError as e:
        print("JSON Parse Error")
        logging.warn("Problem in JSON")
        logging.warn(msg)

        
def mqtt_connect():
    client = MQTTClient(device_ID, mqtt_server, keepalive=6000)
    client.set_callback(sub_cb)
    client.connect()
    print('Connected to %s MQTT Broker'%(mqtt_server))
    mqtt_Status = True
    return client

def reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    time.sleep(5)
    machine.reset()
    #mqtt_connect()
    
def mqtt_Subscribe(topic_sub):
    client.subscribe(topic_sub)
    
def mqtt_Publish(topic_pub, payload):
    client.publish(topic_pub, payload)

def mqtt_Publish_Info(topic_pub):
    device_Info = config_Manager.get_DeviceInfo()
    print("Publishing Device Info: " + device_Info)
    logging.info("Publishing Device Info: " + device_Info)
    client.publish(topic_pub, str(device_Info), retain=True, qos=1)
    

if wlan:
    try:
        client = mqtt_connect()
        print(client)
        logging.info("PicoW Connected to " + str(mqtt_server) + " MQTT Broker")
    except OSError as e:
        logging.error("PicoW Connection Err with " + str(mqtt_server)+ " MQTT Broker")
        reconnect()
        
   
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(s)
    state = s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    bind_state = s.bind(('', 80))
    s.listen(5)
    logging.info("Socket Init")
    
    
    
except:
    print("Bind to IP and Port failed!")
    logging.error("Bind to IP and Port failed!")
    machine.reset()


#### Publishing Device Information for 1 Time
mqtt_Publish_Info(topic_Ip_Result)

counter = 0

######################### Here Is the Main Loop ########################################
while True:
    try:
        currentT = logging.time_string()
        currentT = currentT[0:5]
        print(currentT)
        if (currentT == resetTime):
            time.sleep(60)
            logging.info("schedule Reset !! Device Will Reset in 1 Min!!")
            time.sleep(60)
            machine.reset()
        
        if wifi_Status is True:
            wlan_Led.off()
            nowTime = int(time.time())
            if(nowTime - oldTime >= led_blink_Interval):
                oldTime = nowTime
                wlan_Led.on()
             
            mqtt_Subscribe(topic_Open)
            mqtt_Subscribe(topic_Close)
            mqtt_Subscribe(topic_GetStatus)
            mqtt_Subscribe(topic_ResetDevice)
            mqtt_Subscribe(topic_CheckMqtt)
            
            
            ######################## IF you want to send payload in an Interval ############################
            
            currentMillis = int(time.time())
            
            if(currentMillis - previousMillis >= interval):
                previousMillis = currentMillis
                
                payload = ujson.dumps(
                    {
                        "device_id":device_ID,
                        "device_ip":ip_Address
                    }
                )
                
                mqtt_Publish(topic_Alive, payload)
                print(logging.datetime_string() + " Publishing Payload! " )#+ str(counter))
                #counter = counter + 1
            

            nowMillis = int(time.time())
            
            if(nowMillis - oldMillis >= mqttCheck_PublishInterval):
                oldMillis = nowMillis
                
                mqttCheckPayload = ujson.dumps(
                    {
                        "device_id":device_ID,
                        "mqtt_Status":mqtt_Status
                    }
                )
                
                mqtt_Publish(topic_CheckMqtt, mqttCheckPayload)
                print(logging.datetime_string() + " Publishing Payload! " )#+ str(counter))
                

            check_Mqtt_nowMillis = int(time.time())
            
            if(check_Mqtt_nowMillis - check_Mqtt_oldMillis >= check_Mqtt_Interval):
                check_Mqtt_oldMillis = check_Mqtt_nowMillis
                if(mqtt_Status == False):
                    logging.error("Reseting !! MQTT is Disconnected!!")
                    #machine.reset()
                if(mqtt_Status == True):
                    mqtt_Status = False
                    
                    
                    

                print(logging.datetime_string() + " Publishing Payload! " )#+ str(counter))
            #############################################################################################   
           
           ## If stuck somewhere in the loop it will reset the MicroController
            recentTime = int(time.time())
            while((time.time() - recentTime) > 20):
                logging.error("Resetting!!! Stuck on Somewhere for 20 Second!")
                machine.reset()
        else:
            wlan_Led.off()
            logging.error("Reseting !! Wifi is Disconnected!!")
            machine.reset()
            
    except OSError as e:
        print('Connection closed')
        logging.error("Connection Closed!!")
        machine.reset()
