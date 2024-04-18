import time
import RPi.GPIO as GPIO
from mfrc522reader import MFRC522
#from rpi_ws281x import Adafruit_NeoPixel, Color
#from mfrc522 import SimpleMFRC522
import os
import time
import websocket
import threading
import rel
import asyncio

import sys
CALIBRATE = False


# Variables
numChars = 32
receivedMsg = [''] * numChars
newData = False

# Color RFID HEX
BLUE_COLOR = "96FF2FE0"
GREEN_COLOR = "96F88CF0" #CHANGE THESE TO THE IDS OF YOUR CARDS
YELLOW_COLOR = "C027DDE0"
PURPLE_COLOR = "96F44F10"

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


def setup():
    global ws,reader, isWifiConnected, isWSConnected, isGameStarted, isGameModePlanetHop, isGameModeGuided
    #GPIO.cleanup()
    #GPIO.setmode(GPIO.BOARD)
    
    time.sleep(5)
    ws.connect("ws://192.168.0.115:5045/")
    if "Conn" in ws.recv():
        isWSConnected=True;
        isWifiConnected=True;
        print('WSC Connected')
    
    time.sleep(1)
# RFID Sensor Setup

    # Hardware Serial UART Communication between Raspberry Pi and NodeMCU module
    print("Serial communication initialized")

    # Initiate the RFID sensor instance
    print("Initializing RFID sensor")
    # No setup required for RFID on Raspberry Pi


def loop():
    global Check, Check2


    if not isWifiConnected and not isGameStarted:  # no wifi connection, empty for now. Can expand later
       pass

    if isWifiConnected and not isWSConnected and not isGameStarted:  # no websocket connection, empty for now. Can expand later
        pass

    if isWifiConnected and isWSConnected and not Check:  # standby mode , empty for now. Can expand later
        Check=True
        process_new_data() #get messages from open lib
  

    if isWifiConnected and isWSConnected and isGameStarted and not Check2:  # game started
        Check2=True
        detect_rfid_tag() #Start RFID Scanning

    if isWifiConnected and not isWSConnected and isGameStarted:  # Error state
        pass

    if CALIBRATE and not Check2:
        Check2=True
        detect_rfid_tag() #Start RFID Scanning



def process_new_data(): #function to  get data from open lib
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
           
            
    threading.Thread(target=run).start() #Start a thread to allow for rfid and messages to work


def detect_rfid_tag(): #function to start RFID sensor
    reader = MFRC522()
    time.sleep(1)
    def run(*args):
        print('in RFID')
        while(True):
            try:
                uid = reader.read_uid()
                if uid:
                    uid_str = uid
                    
                    print(uid_str)
                    determine_color_from_rfid(uid_str)
            except Exception as e:
                print("Error reading RFID:", str(e))
                
    threading.Thread(target=run).start()


def determine_color_from_rfid(uid_str): #function to process scanned rfid and send message to open lib
    global ws,isGameStarted, blueCaptured, greenCaptured, yellowCaptured, purpleCaptured
    detected_id = uid_str  # Remove '0x' prefix
   
    
    if not isGameStarted :
        return;
    print('in color')
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




def reset_color_detection(): #reset state
    global blueCaptured, greenCaptured, yellowCaptured, purpleCaptured
    blueCaptured = False
    greenCaptured = False
    yellowCaptured = False
    purpleCaptured = False


def reset_game_start_state(): #reset state
    global isGameStarted, isGameModePlanetHop, isGameModeGuided
    print('reseting state')
    os.execl(sys.executable,sys.executable,*sys.argv)
    isGameStarted = False
    isGameModePlanetHop = False
    isGameModeGuided = False
   
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
