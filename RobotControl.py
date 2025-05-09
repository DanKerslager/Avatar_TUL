# -*- coding: utf-8 -*-

from naoqi import ALProxy
import wx
import time

from SSHClient import SSHClient
from SoundWorker import SoundWorker
from VideoWorker import VideoWorker
from MovementWorker import MovementWorker
from TimelineWorker import TimelineWorker


class RobotControl:
    def __init__(self, nao_ip, nao_port, wxmain, timelines):
        """Connect to robot, initiate variables and functions"""
        self.wxmain = wxmain

        # Prepares tts and sets its parameters
        self.tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)  # plain text to speech
        self.tts.setParameter("speed", 80)
        self.tts_animated = ALProxy("ALAnimatedSpeech", nao_ip, nao_port)  # text to speech animated
        self.tts_animated.setBodyLanguageMode(1)  # Animated Speech
        self.eyeFollower = ALProxy("ALBasicAwareness", nao_ip, nao_port)  # eye follower
        self.audio = ALProxy("ALAudioDevice", nao_ip, nao_port)  # audio module
        self.leds_light = ALProxy("ALLeds", nao_ip, nao_port)
        self.battery = ALProxy("ALBattery", nao_ip, nao_port)
        self.get_battery_charge()

        # Set up Movement client
        self.movement = MovementWorker(wxmain, nao_ip, nao_port)
        # Turns off autonomous life
        self.life = ALProxy("ALAutonomousLife", nao_ip, nao_port)
        self.life.setState("disabled")
        # Set up Timeline client
        self.timelines = TimelineWorker(timelines, wxmain, nao_ip, nao_port)

        try:
            # Set up SSH client
            self.ssh_client = SSHClient(server=nao_ip, username="nao", password="nao")
            # Sets up LIVE robot audio stream
            self.ssh_client.run_ssh_command(
                "gst-launch-0.10 pulsesrc ! audioconvert ! audioresample ! audio/x-raw-float,rate=44100,channels=2 ! tcpserversink port=1234 sync=false")
            
            # Sets up catching the LIVE stream
            #self.sound_streamer = SoundWorker("sound_streamer", "tcp://" + nao_ip + ":1234")
            self.sound_streamer = SoundWorker(nao_ip, 1234)

            self.sound_streamer.start_stream()
        except Exception as e:
            print("Error setting up SSH or audio stream:", e)
        # Sets up video stream
        self.video = VideoWorker(wxmain, nao_ip, nao_port)
        print("CONNECTED")

    def get_battery_charge(self):
        battery_charge = "N/A"
        try:
            battery_charge = str(self.battery.getBatteryCharge())
        except:
            print("Failed")
        self.wxmain.battery_label_val.SetLabel(battery_charge)
        wx.CallLater(1000, self.get_battery_charge)

    def tts_command(self, text):
        self.tts.setLanguage(self.wxmain.language)
        self.tts_animated.say(text.encode("utf-8"))
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

    def reset_eyes(self):
        self.eyeFollower.startAwareness()

    def close(self):
        self.video.on_close()
        self.movement.go_pose("Crouch")
        time.sleep(3)
        self.movement.rest()
        self.sound_streamer.stop_stream()
        print("robot unsubscribed")
