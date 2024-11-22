#!/usr/bin/env python3
#https://thelinuxcode.com/send_receive_udp_python/

from ev3dev2.motor import OUTPUT_A, OUTPUT_D, SpeedPercent, MoveTank
from ev3dev2.sensor import INPUT_4
from ev3dev2.sensor.lego import UltrasonicSensor
from ev3dev2.sound import Sound

import socket
import sys
import time
import os.path

### robot init
tank_drive = MoveTank(OUTPUT_A, OUTPUT_D)
ultrasonic = UltrasonicSensor(INPUT_4)
speaker = Sound()

### UDP
SERVER_IP = "100.64.0.101"
ROBOT_IP = "100.64.0.100"
SENDING_PORT = 42070
RECIEVING_PORT = 42069
message = ""
ping_request = False
ping_message = ""
# last_distance_send = time.ctime()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ROBOT_IP, RECIEVING_PORT))
sock.setblocking(False)  # Nastavení neblokujícího režimu


print("Listening for traffic at ("+str(ROBOT_IP)+", "+str(RECIEVING_PORT)+")")
print("Screaming traffic at ("+str(SERVER_IP)+", "+str(SENDING_PORT)+")")


def obstacle_distance(ultrasonic):
    return ultrasonic.distance_centimeters()

try:
  while True:
      try:
        data, address = sock.recvfrom(4096)
        payload = str(data.decode())
        print("Recieved data:\t" + payload)

        command = payload.split("@@@")

        # if (not command.startswith("LEGOCTRL")):
        #   message = "Unaccetable command: " + payload
        #   print(message)
        #   continue
        
        command = payload.split("#")

        if (command[1] == "STOP"):
          tank_drive.stop()

        elif (command[1] == "RIDE"):
          if (command[2] == "0"):
            tank_drive.on(int(command[3]), int(command[4]))
          else:
            tank_drive.on_for_seconds(int(command[3]), int(command[4]), int(command[2]))
        
        elif (command[1] == "SONG"):
          if (int(command[3]) > 100):
            speaker.set_volume(100)
            speaker.play_file(command[2], 100, Sound.PLAY_NO_WAIT_FOR_COMPLETE)
          else:
            speaker.set_volume(int(command[3]))
            speaker.play_file(command[2], int(command[3]), Sound.PLAY_NO_WAIT_FOR_COMPLETE)
          # speaker.play_file(command[2], int(command[3]), Sound.PLAY_LOOP)
          
        elif (command[1] == "MUTE"):
          ## Varianta 1
          # speaker = None
          # speaker = Sound()

          ## Varianta 2
          speaker.tone(444, 0.2)
          speaker.set_volume(0)

        else:
          message = "Command "+command[1]+" is UNKOWN!"
      except BlockingIOError:
        # nic nepřišlo
        pass


      if (message != ""):
        message = "@@@LEGOCTRL#MESSAGE#0#" + message
        sock.sendto(message.encode(), (SERVER_IP, SENDING_PORT))
      #message = str(payload) + "\t-\t" + drive_arrow(payload)

      
      # if ( (last_distance_send + 300) <= time.ctime() ):
      #   message = "@@@LEGOCTRL#SENSOR#4#" + obstacle_distance
      #   sock.sendto(message.encode(), (SERVER_IP, SENDING_PORT))
      #   last_distance_send = time.ctime()

      # sock.sendto(message.encode(), address)
except Exception as e:
  print("exception: " + str(e))
  tank_drive.stop()
  sock.close()