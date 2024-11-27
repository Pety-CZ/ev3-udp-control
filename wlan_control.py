#!/usr/bin/env python3
#https://thelinuxcode.com/send_receive_udp_python/

#TODO
#
#https://forums.raspberrypi.com/viewtopic.php?f=32&t=85601#p604902
#
#

from ev3dev2.motor import OUTPUT_A, OUTPUT_D, SpeedPercent, MoveTank, MoveJoystick
from ev3dev2.sensor import INPUT_4
from ev3dev2.sensor.lego import UltrasonicSensor
from ev3dev2.sound import Sound

import socket
import sys
import os
import time
from pathlib import Path
import subprocess

### robot init
tank_drive = MoveTank(OUTPUT_A, OUTPUT_D)
joystick_drive = MoveJoystick(OUTPUT_A, OUTPUT_D)
ultrasonic = UltrasonicSensor(INPUT_4)
speaker = Sound()
last_song = ""
PLAYLIST_DIR = "./playlist/"
last_distance_send = time.time()
distance_send_delay = 0.25      # in seconds

### UDP
SERVER_IP = "100.64.0.101"
ROBOT_IP = "100.64.0.100"
SENDING_PORT = 42070
RECIEVING_PORT = 42069
message = ""
ping_message = ""

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ROBOT_IP, RECIEVING_PORT))
sock.setblocking(False)  # Nastavení neblokujícího režimu

def transmit_playlist(msg):
    music_files = []
    for i in os.listdir(PLAYLIST_DIR):
        if i.endswith(".wav"):
            music_files.append(i)
    music_files.sort()

    #playlist = "@@@LEGOCTRL#PING#1#"
    playlist = msg
    for file in music_files:
        playlist = playlist + "#SONG#" + file
        # message = "@@@LEGOCTRL#PLAYLIST#"+i+"#" + file
        # sock.sendto(message.encode(), (SERVER_IP, SENDING_PORT))
    transmit("playlist", playlist)

def check_boundaries(value, min, max):
  if value > max:
    return max
  elif value < min:
    return min
  else:
    return value
  

def transmit(type_of_message, message):
    if (message != ""):
        if (type_of_message == "error"):
            message = "@@@LEGOCTRL#MESSAGE#0#" + message
            sock.sendto(message.encode(), (SERVER_IP, SENDING_PORT))

        elif (type_of_message == "ping_reply"):
            ping_message = "@@@LEGOCTRL#PING#1#" + ping_message
            sock.sendto(ping_message.encode(), (SERVER_IP, SENDING_PORT))

        elif (type_of_message == "playlist"):
            sock.sendto(message.encode(), (SERVER_IP, SENDING_PORT))


def play_music(filename, volume):
    speaker.play_file(filename, volume, Sound.PLAY_NO_WAIT_FOR_COMPLETE)


def music_playing_check(param): # LOOP, KILL
    # Gets process list
    process_list = subprocess.check_output(["ps", "aux"]).decode()

    # Search for process /usr/bin/aplay
    aplay_process = subprocess.Popen(["grep", "/usr/bin/aplay"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = aplay_process.communicate()

    # Gets PID of proces
    if output:
        if ( param == "KILL" ):
                pid = output.split()[1]
                # Kills PID
                subprocess.Popen(["kill", "-9", pid])
    elif ( param == "LOOP" ):
        play_music(last_song, speaker.get_volume())



####### NOT TESTED !!! #########
def stop_music():
    # Gets process list
    process_list = subprocess.check_output(["ps", "aux"]).decode()

    # Search for process /usr/bin/aplay
    aplay_process = subprocess.Popen(["grep", "/usr/bin/aplay"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = aplay_process.communicate()

    # Gets PID of proces
    if output:
        pid = output.split()[1]
        # Kills PID
        subprocess.Popen(["kill", "-9", pid])
    else:
        print("Proces /usr/bin/aplay nebyl nalezen.")


# def transmit_message(message):
#   if (message != ""):
#     message = "@@@LEGOCTRL#MESSAGE#0#" + message
#     sock.sendto(message.encode(), (SERVER_IP, SENDING_PORT))

# def ping_response(ping_message):
#   if (ping_message != ""):
#     ping_message = "@@@LEGOCTRL#PING#1#" + ping_message
#     sock.sendto(ping_message.encode(), (SERVER_IP, SENDING_PORT))
def now():
    return time.time()

def transmit_ultrasonic():
  if ( (last_distance_send + distance_send_delay) <= now() ):
    message = "@@@LEGOCTRL#SENSOR#4#" + obstacle_distance
    sock.sendto(message.encode(), (SERVER_IP, SENDING_PORT))
    last_distance_send = now()

def obstacle_distance(ultrasonic):
    return ultrasonic.distance_centimeters()

try:
    print("Listening for traffic at ("+str(ROBOT_IP)+", "+str(RECIEVING_PORT)+")")
    print("Screaming traffic at ("+str(SERVER_IP)+", "+str(SENDING_PORT)+")")
    transmit_playlist()
    speaker.set_volume(100)
    speaker.tone(444, 0.5)
    speaker.set_volume(30)
    while True:
        try:
            message = ""
            ping_message = ""
            data, address = sock.recvfrom(4096)
            payload = str(data.decode())
            # print("Recieved data:\t" + payload) 

            if ( not payload.startswith("@@@LEGOCTRL")):
                print("Not start with '@@@'")
                message = "Unknown payload!"
                transmit("error", message)
                continue
                
            cmd = payload.split("#")
            command = cmd[1]

            # creates array of params
            param_length = len(cmd)
            param =  []
            param.append("")     # creates "empty" index 0, so that index number matches param number
            for i in  range(2, param_length): # has to begin from 2 to load only params
                param.append(cmd[i])


            if (command == "STOP"):
                tank_drive.stop()

            elif (command == "RIDE"):
                seconds = check_boundaries(float(param[1]), 0.0, 10.0)
                l_speed = check_boundaries(int(param[2]), -100, 100)
                r_speed = check_boundaries(int(param[3]), -100, 100)
                if (seconds == 0.0):
                    tank_drive.on(l_speed, r_speed)
                else:
                    tank_drive.on_for_seconds(l_speed, r_speed, seconds)
            
            elif (command == "JOYSTICK"):
                x = check_boundaries(int(param[1]), -100, 100)
                y = check_boundaries(int(param[2]), -100, 100)
                joystick_drive.on(x, y, 100)

            elif (command == "SONG"):
                filename = param[1]
                # volume = check_boundaries(int(param[2]), 0, 100)
                volume = speaker.get_volume()

                file = PLAYLIST_DIR + Path(filename)
                if not file.is_file():
                    message = "Song with filename '" + filename + "' does not exist!"
                    continue
                # stop_music();
                music_playing_check("KILL");
                last_song = file
                speaker.set_volume(volume)
                speaker.play_file(filename, volume, Sound.PLAY_NO_WAIT_FOR_COMPLETE)
            # speaker.play_file(command[2], int(command[3]), Sound.PLAY_LOOP)
        
            elif (command == "VOLUME"):
                volume = check_boundaries(int(param[1]), 0, 100)
                speaker.set_volume(volume)

            elif (command == "MUTE"):
                ## Varianta 2
                # speaker.tone(444, 0.2)
                speaker.set_volume(0)

            elif (command == "PING"):
                if (param[1] == "0"):
                    msg = "@@LEGOCTRL#" + command + "#1#" + param[2]  # param 2 --> PING SYN
                    transmit_playlist(msg);

            elif (command == "TONE"):
                music_playing_check("KILL")
                frequency = check_boundaries(int(param[1]), 0, 100)
                duration = 42069
                speaker.play_tone(frequency, duration)
                
            else:
                message = "Command '" + command + "' is UNKOWN!"

            music_playing_check("LOOP")
            transmit("error", message)
            transmit("ping_reply", ping_message)
            # transmit_message(message)
            # ping_response(ping_message)
            transmit_ultrasonic()

        except BlockingIOError:
        # no message recieved
            pass

except Exception as e:
  print("exception: " + str(e))
  tank_drive.stop()
  speaker.set_volume(100)
  speaker.speak("I am dead,  n E ga!")
  sock.close()