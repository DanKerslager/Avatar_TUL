# -*- coding: utf-8 -*-

from naoqi import ALProxy
import wx
import time

from SSHClient import SSHClient
from SoundWorker import SoundWorker
from VideoWorker import VideoWorker
from MovementWorker import MovementWorker


class RobotControl:
    def __init__(self, nao_ip, nao_port, wxmain):
        """Connect to robot, initiate variables and functions"""
        self.wxmain = wxmain

        # Prepares tts and sets its parameters
        self.tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)  # plain text to speech
        self.tts.setParameter("speed", 80)
        self.tts_animated = ALProxy("ALAnimatedSpeech", nao_ip, nao_port)  # text to speech animated
        self.tts_animated.setBodyLanguageMode(1)  # Animated Speech
        # Turns off autonomous life
        self.life = ALProxy("ALAutonomousLife", nao_ip, nao_port)
        self.life.setState("safeguard")

        self.leds_light = ALProxy("ALLeds", nao_ip, nao_port)
        self.battery = ALProxy("ALBattery", nao_ip, nao_port)
        self.get_battery_charge()

        # Set up Movement client
        self.movement = MovementWorker(wxmain, nao_ip, nao_port)

        # Set up SSH client
        self.ssh_client = SSHClient(server=nao_ip, username="nao", password="nao")
        # Sets up LIVE robot audio stream
        self.ssh_client.run_ssh_command(
            "gst-launch-0.10 pulsesrc ! audioconvert ! audio/x-raw-int,rate=44100,channels=2,depth=16 ! tcpserversink port=1234")
        # Sets up vlc catching the LIVE stream
        #self.sound_streamer = SoundWorker("sound_streamer", "tcp://" + nao_ip + ":1234")
        self.sound_streamer = SoundWorker(nao_ip, 1234)

        self.sound_streamer.start_stream()
        # Sets up video stream
        self.video = VideoWorker(wxmain, nao_ip, nao_port)
        print "CONNECTED"

    def get_battery_charge(self):
        battery_charge = "N/A"
        try:
            battery_charge = str(self.battery.getBatteryCharge())
        except:
            print("Failed")
        self.wxmain.battery_label_val.SetLabel(battery_charge)
        wx.CallLater(1000, self.get_battery_charge)

    def tts_command(self, text):
        self.tts_animated.say(str(text))
        self.movement.reset_pose()

    def active(self, val):
        if val:
            self.movement.go_pose("Crouch")
            time.sleep(3)
            self.movement.rest()
            self.leds_light.off("FaceLeds")
        else:
            self.movement.go_pose("Crouch")
            self.leds_light.on("FaceLeds")

    def close(self):
        self.video.on_close()
        self.movement.go_pose("Crouch")
        time.sleep(3)
        self.movement.rest()
        self.sound_streamer.stop_stream()
        print("robot unsubscribed")
