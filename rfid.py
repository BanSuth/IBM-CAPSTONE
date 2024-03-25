import time
import RPi.GPIO as GPIO
from mfrc522reader import MFRC522
from rpi_ws281x import Adafruit_NeoPixel, Color
import os
import time
import websocket
import websockets as WEB
import threading
import rel
import asyncio

CALIBRATE = True

# RFID Sensor Setup
reader = MFRC522()




# WS2811 LED Setup
NUM_LEDS = 7
LED_PIN = 18  # GPIO 18
BRIGHTNESS = 255
#strip = Adafruit_NeoPixel(NUM_LEDS, LED_PIN, 800000, 10, False, BRIGHTNESS)
#strip.begin()

# Rover Headlights Setup
ROVER_HEADLIGHTS = 7
#GPIO.setmode(GPIO.BOARD)
#GPIO.setup(ROVER_HEADLIGHTS, GPIO.OUT)

# Variables
numChars = 32
receivedMsg = [''] * numChars
newData = False

# Color RFID HEX
BLUE_COLOR = "96FF2FE0"
GREEN_COLOR = "96F88CF0"
YELLOW_COLOR = "C027DDE0"
PURPLE_COLOR = "96F44F10"

# Rover Lights
led_on = False
gHue = 0
previousMillis = 0
previousMillis_blink = 0
previousMillis_cycle = 0
blink_interval = 0.5  # seconds
breath_interval = 0.02  # seconds

# Rover headlights/taillights
previousMillis_Headlights = 0
headLightState = GPIO.LOW
headlight_interval = 0.5  # seconds

# Planet Detection
blueCaptured = False
greenCaptured = False
yellowCaptured = False
purpleCaptured = False

# Game Configuration
isWifiConnected = False
isWSConnected = False
isGameStarted = False
isGameModePlanetHop = False
isGameModeGuided = False
ws = websocket.WebSocket()
Check= False
Check2= False

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")

async def hello():
     async with WEB.connect("ws://192.168.0.115:5045/") as ws:
        greeting = await ws.recv()
        print(f"{greeting}")
def setup():
    global ws,isWifiConnected, isWSConnected, isGameStarted, isGameModePlanetHop, isGameModeGuided
    GPIO.cleanup()
    #GPIO.setmode(GPIO.BOARD)
    
    

    time.sleep(4)
    #sockConn.send("Hello, world".encode())   
    detect_rfid_tag()
    time.sleep(10)
    asyncio.run(hello());
    #ws.connect("ws://192.168.0.115:5045/")
    #if "Conn" in ws.recv():
     #   isWSConnected=True;
      #  isWifiConnected=True;
      #  print('here')
        
    # Hardware Serial UART Communication between Raspberry Pi and NodeMCU module
    print("Serial communication initialized")

    # Initiate the RFID sensor instance
    print("Initializing RFID sensor")
    # No setup required for RFID on Raspberry Pi


def loop():
    global Check, Check2

    
    # Check for incoming messages from NodeMCU
     # receive_msgs_with_start_end_markers()
    

    if not isWifiConnected and not isGameStarted:  # no wifi connection
       pass
       # blink_rover_leds(Color(255, 0, 0), True)

    if isWifiConnected and not isWSConnected and not isGameStarted:  # no websocket connection
        pass
        #breath_color_leds()

    if isWifiConnected and isWSConnected and not Check:  # standby mode
        Check=True
        process_new_data()
        #blink_rover_head_lights()
        #turn_on_rover_leds(Color(0, 255, 255), True)

    if isWifiConnected and isWSConnected and isGameStarted and not Check2:  # game started
        #turn_on_rover_head_lights()
        #turn_on_rover_leds(Color(0, 255, 255), True)
        Check2=True
        #detect_rfid_tag()

    if isWifiConnected and not isWSConnected and isGameStarted:  # Error state
        pass
        #turn_on_rover_leds(Color(255, 0, 0), False)

    if CALIBRATE:
        pass
        #detect_rfid_tag()


def receive_msgs_with_start_end_markers():
    global newData, receivedMsg
    startMarker = '<'
    endMarker = '>'
    recvInProgress = False
    ndx = 0

    while len(receivedMsg) < numChars and not newData:
        rc = input()  # Replace this line with actual code to read from serial
        if recvInProgress:
            if rc != endMarker:
                receivedMsg[ndx] = rc
                ndx += 1
            else:
                receivedMsg[ndx] = ''
                recvInProgress = False
                ndx = 0
                newData = True
        elif rc == startMarker:
            recvInProgress = True


def process_new_data():
    def run(*args):
        global newData, isWifiConnected, isWSConnected, isGameStarted, isGameModePlanetHop, isGameModeGuided
        print('in msg process')
        while(True):
            msg = ws.recv()
            if msg == "GS":
                print('Got MSG: '+msg)
                isGameStarted = True
            elif msg == "GM":
                isGameStarted = True
                isGameModeGuided = True
            elif msg == "PH":
                isGameStarted = True
                isGameModePlanetHop = True
            elif msg == "GE":
                reset_game_start_state()
           
            
    threading.Thread(target=run).start()


def detect_rfid_tag():
    print('in RFID')
    def run(*args):
        while(True):
            try:
                id = reader.read_uid()
                if id:
                    uid_str = id 
                    #format(id, 'X')
                    #uidbytes = id.tobytes((id.bitlength() + 7) // 8, byteorder='big')
                    print(uid_str)
                    determine_color_from_rfid(uid_str)
            except Exception as e:
                print("Error reading RFID:", str(e))
    threading.Thread(target=run).start()


def determine_color_from_rfid(uid_str):
    global ws,isGameStarted, blueCaptured, greenCaptured, yellowCaptured, purpleCaptured
    detected_id = uid_str  # Remove '0x' prefix
    
    if not isGameStarted :
        return;
    
    uid_len = len(detected_id)
    

    if detected_id == YELLOW_COLOR:
        if not yellowCaptured:
            print("<YW>")
            ws.send("YW");
            #activate_rover_planet_collection_light(Color(255, 165, 0))  # Orange color
            if not isGameModePlanetHop and not isGameModeGuided:
                yellowCaptured = True
    elif detected_id == PURPLE_COLOR:
        if not purpleCaptured:
            print("<PUR>")
            ws.send("PUR");
            #activate_rover_planet_collection_light(Color(128, 0, 128))  # Purple color
            if not isGameModePlanetHop and not isGameModeGuided:
                purpleCaptured = True
    elif detected_id == BLUE_COLOR: 
        if not blueCaptured:
            print("<BLU>")
            ws.send("BLU");
            #activate_rover_planet_collection_light(Color(0, 0, 255))  # Blue color
            if not isGameModePlanetHop and not isGameModeGuided:
                blueCaptured = True
    elif detected_id == GREEN_COLOR: 
        if not greenCaptured:
            print("<GRN>")
            ws.send("GRN");
            #activate_rover_planet_collection_light(Color(0, 255, 0))  # Green color
            if not isGameModePlanetHop and not isGameModeGuided:
                greenCaptured = True
    else:
        ws.send("RED")
        #blink_rover_damage_lights()

def fill_breath_color_leds():
    global gHue
    for i in range(NUM_LEDS - 1):
        strip.setPixelColor(i, strip.ColorHSV(gHue, 255, 255))
    strip.show()


def breath_color_leds():
    global gHue, previousMillis, breath_interval
    current_millis = time.time()
    if current_millis - previousMillis >= breath_interval:
        previousMillis = current_millis
        fill_breath_color_leds()
        gHue += 1


def blink_rover_leds(color, skip_canopy_light):
    global led_on, previousMillis_blink, blink_interval
    current_millis = time.time()
    if current_millis - previousMillis_blink >= blink_interval:
        previousMillis_blink = current_millis
        if not led_on:
            turn_on_rover_leds(color, skip_canopy_light)
            led_on = True
        else:
            turn_off_rover_leds()
            led_on = False


def turn_on_canopy_light(color):
    strip.setPixelColor(6, color)
    strip.show()


def turn_off_canopy_light():
    strip.setPixelColor(6, 0)
    strip.show()


def turn_on_rover_leds(color, skip_canopy_light):
    num_of_leds_minus_canopy = NUM_LEDS
    if skip_canopy_light:
        num_of_leds_minus_canopy = NUM_LEDS - 1
        turn_off_canopy_light()
    for i in range(num_of_leds_minus_canopy):
        strip.setPixelColor(i, color)
    strip.show()


def turn_off_rover_leds():
    for i in range(NUM_LEDS):
        strip.setPixelColor(i, 0)
    strip.show()


def blink_rover_head_lights():
    global headLightState, previousMillis_Headlights, headlight_interval
    current_millis = time.time()
    if current_millis - previousMillis_Headlights >= headlight_interval:
        previousMillis_Headlights = current_millis
        if headLightState == GPIO.LOW:
            headLightState = GPIO.HIGH
        else:
            headLightState = GPIO.LOW
        GPIO.output(ROVER_HEADLIGHTS, headLightState)


def activate_rover_planet_collection_light(planet_color):
    interval = 1.5  # seconds
    turn_off_all_lights()
    turn_on_canopy_light(planet_color)
    start_millis = time.time()
    end_millis = start_millis
    while end_millis - start_millis <= interval:
        cycle_planet_capture_led(planet_color)
        end_millis = time.time()
    turn_on_rover_leds(Color(0, 255, 255), True)


def cycle_planet_capture_led(planet_color):
    for i in range(NUM_LEDS - 1):
        strip.setPixelColor(i, planet_color)
        strip.show()
        time.sleep(0.15)
        strip.setPixelColor(i, 0)
        strip.show()


def blink_rover_damage_lights():
    turn_on_rover_leds(Color(139, 0, 0), False)  # DarkRed color
    time.sleep(1)
    turn_on_rover_leds(Color(0, 255, 255), True)  # Turquoise color


def turn_on_rover_head_lights():
    GPIO.output(ROVER_HEADLIGHTS, GPIO.HIGH)


def turn_off_rover_head_lights():
    GPIO.output(ROVER_HEADLIGHTS, GPIO.LOW)


def turn_off_all_lights():
    turn_off_canopy_light()
    for i in range(NUM_LEDS):
        strip.setPixelColor(i, 0)
    strip.show()
    turn_off_rover_head_lights()


def reset_color_detection():
    global blueCaptured, greenCaptured, yellowCaptured, purpleCaptured
    blueCaptured = False
    greenCaptured = False
    yellowCaptured = False
    purpleCaptured = False


def reset_game_start_state():
    global isGameStarted, isGameModePlanetHop, isGameModeGuided
    print('reseting state')
    isGameStarted = False
    isGameModePlanetHop = False
    isGameModeGuided = False
    #turn_off_all_lights()
    reset_color_detection()


if __name__ == "__main__":
    setup()
    try:
        while True:
            loop()
    except KeyboardInterrupt:
        print("Program terminated by user.")
    finally:
        GPIO.cleanup()
