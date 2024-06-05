# -*- coding: utf-8 -*-
from naoqi import ALBroker
from naoqi import ALModule
from naoqi import ALProxy
from PIL import Image, ImageTk
import time
import random
import threading
import vlc # audio replay
import paramiko  # SSHClient
import traceback
import tkFont
import wx
import uuid

"""
PŘEDPOKLADY:
python 2.7(.18) (32bit!)
balíčky:
Vlc (32bit)
    https://get.videolan.org/vlc/3.0.20/win32/vlc-3.0.20-win32.exe (32bit!)
    Možné problémy s DLL a přidáním do PATH
  
python-vlc v2.2 (v3.0)
    pip install python-vlc==3.0.20123

paramiko 2.12
    "pip install paramiko==2.12.0"

naoqi
    (https://community-static.aldebaran.com/resources/2.1.4.13/sdk-python/pynaoqi-2.1.4.13.win32.exe)
wx: "pip install wxpython==4.0.0.0"


extra: přidat možnost ovládání pohybu hlavy (3D prostorově?)
extra: bind tlačítek na klávesnici pro ovládání robota (možná i přes ovladač?)
extra: upravení pole příkazů (commmands) aby se na UI vykreslovalo automaticky podle možných použitelných
extra: nastavitelnost rychlosti pohybu - frekvence a krok - pomoci slidebarů
extra: reset kamery přes naoqi SSH (vypadá na jediné řešení?) - nebo-li bez komplet restartu robota
extra: extra funkce tlačítek než jen fakty
extra: světla na robotovi, nějaký efekty když provádi akce/mluví apod
extra: CZ a EN jazyk přepnutí
"""

thread = threading.Event()
process = None


class SSHClient:
    def __init__(self, server, username=None, password=None, port=22):
        """Init SSH connection to server etc, url changeable to username, ip etc.."""
        self.port = port
        self.username = username
        self.server = server
        self.password = password
        self.client = paramiko.SSHClient()

    def connect(self):
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # "bad" security", meant for private network
        self.client.connect(self.server, username=self.username, password=self.password, port=self.port)

    def run_ssh_command(self, cmd_command):
        ssh_stdin, ssh_stdout, ssh_stderr = self.client.exec_command(cmd_command)
        print "SSH says.."
        print ssh_stdin
        print ssh_stdout
        print ssh_stderr
        print "======================"

class RobotControlFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(RobotControlFrame, self).__init__(*args, **kw)
        self.SetSize((800, 600))
        self.SetTitle("Sekretářka Nao")

        self.ip_val = "192.168.0.122"
        self.port_val = "9559"
        self.robot_volume = 60
        self.app_volume = 60

        try:
            with open("ip_port.txt", "r+") as file:
                data = file.read().splitlines()
                self.ip_val = str(data[0])
                self.port_val = str(data[1])
        except Exception:
            print("Unable to read file to load parameters, using default ones")

        try:
            with open("sound_config.txt", "r+") as file:
                data = file.read().splitlines()
                self.robot_volume = int(data[0])
                self.app_volume = int(data[1])
        except Exception:
            print("Unable to read file to load sound parameters, using default ones")

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Initialize widgets
        self.status = wx.StaticText(self.panel, label="Status: Not Connected")
        self.sizer.Add(self.status, 0, wx.ALL | wx.EXPAND, 10)
        self.ip_entry = wx.TextCtrl(self.panel, value=self.ip_val)
        self.port_entry = wx.TextCtrl(self.panel, value=self.port_val)
        self.tts_entry = wx.TextCtrl(self.panel, value="Enter text to speak here..", size=(400, -1))
        self.transcript_field = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, size=(400, 150))

        self.confirm_button = wx.Button(self.panel, label="Connect")
        self.disconnect_button = wx.Button(self.panel, label="Disconnect/reset")
        self.sit_button = wx.Button(self.panel, label="Sit")
        self.stand_button = wx.Button(self.panel, label="Stand")

        self.move_forward_button = wx.Button(self.panel, label="^", size=(50, 50))
        self.rotate_left_button = wx.Button(self.panel, label=">", size=(50, 50))
        self.rotate_right_button = wx.Button(self.panel, label="<", size=(50, 50))

        self.switch_camera_button = wx.Button(self.panel, label="Switch Camera")
        self.tts_button = wx.Button(self.panel, label="Send text")
        #self.close_button = wx.Button(self.panel, label="Close")

        # Volume Sliders
        self.vol_slider_robot = wx.Slider(self.panel, value=self.robot_volume, minValue=0, maxValue=100, style=wx.SL_VERTICAL)
        self.vol_slider_app = wx.Slider(self.panel, value=self.app_volume, minValue=0, maxValue=100, style=wx.SL_VERTICAL)


        # Initialize video player
        self.video_player = wx.StaticBitmap(self.panel, size=(640, 480))
        self.video_player.SetBackgroundColour(wx.BLACK)

        self.battery_label = wx.StaticText(self.panel, label="Battery:")
        self.battery_label_val = wx.StaticText(self.panel, label="N/A")

        self.create_widgets()

        self.panel.SetSizer(self.sizer)
        self.sizer.Fit(self)

        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down) #bind keys

    def on_close(self, event):
        # Perform cleanup tasks here
        """Disconnect from all services and release resources."""        
        # Destroy the frame and exit the application
        self.Destroy()
        wx.GetApp().ExitMainLoop()
    

    class SoundWorker(ALModule):
        def __init__(self, name, url):
            """Sets up media player"""
            name = name + str(uuid.uuid4())  # Append a unique identifier
            ALModule.__init__(self, name)
            self.BIND_PYTHON(self.getName(), "callback")
            self.module_name = name 
            self.name = name
            # self.url = "tcp://" + ip + ":" + port
            self.instance = vlc.Instance()
            self.player = self.instance.media_player_new()
            self.media = self.instance.media_new(url)
            self.player.set_media(self.media)
            print "setting up audio stream, url:", url
            
        def start_stream(self):
            self.player.play()

        def stop_stream(self):
            self.player.stop()

        def change_volume(self, new_volume):
            print "updating volume"
            print new_volume
            self.player.audio_set_volume(int(new_volume))

    def play_nao_video(self):
        """Subscribe to nao camera with given pamarameters"""
        # 2 - VGA. 11 - colorspace RGB
        # http://doc.aldebaran.com/2-1/family/robots/video_robot.html#cameracolorspace-mt9m114
        
        time.sleep(1)
        resolution = 1    # 0 for 320x240, 1 for 640x480
        color_space = 11  # 11 for RGB
        fps = 20
        self.video_client = self.camera.subscribeCamera("python_client", self.camera_index, resolution, color_space, fps)
        if not self.video_client:
            print("Failed to subscribe to camera")
            return
        print self.video_client

        # Start retrieving and displaying video frames
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_video, self.timer)
        self.timer.Start(1000 // fps)
        print("timer started")

        self.Show()
        
    def update_video(self, event):
        nao_image = self.camera.getImageRemote(self.video_client)
        if nao_image:
            img = wx.Image(nao_image[0], nao_image[1], nao_image[6])
            img = img.Scale(640, 480)
            bitmap = wx.Bitmap(img)
            self.video_player.SetBitmap(bitmap)

    def tts_command(self, text):
        self.tts_animated.say(str(text))
        self.reset_pose(self.LAST_POSE)

    
    def create_widgets(self):
        # Top Section (IP, Port, Connect, Disconnect, Sit, Stand, Battery)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer.Add(wx.StaticText(self.panel, label="IP:"), 0, wx.ALL | wx.EXPAND, 5)
        top_sizer.Add(self.ip_entry, 0, wx.ALL | wx.EXPAND, 5)
        top_sizer.Add(wx.StaticText(self.panel, label="PORT:"), 0, wx.ALL | wx.EXPAND, 5)
        top_sizer.Add(self.port_entry, 0, wx.ALL | wx.EXPAND, 5)
        top_sizer.Add(self.confirm_button, 0, wx.ALL | wx.EXPAND, 5)
        top_sizer.Add(self.disconnect_button, 0, wx.ALL | wx.EXPAND, 5)
        top_sizer.Add(self.battery_label, 0, wx.ALL | wx.EXPAND, 5)
        top_sizer.Add(self.battery_label_val, 0, wx.ALL | wx.EXPAND, 5)
        # top_sizer.Add(self.close_button, 0, wx.ALL | wx.EXPAND, 5)

        self.sizer.Add(top_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Left Section (Volume Sliders)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(wx.StaticText(self.panel, label="Robot Volume"), 0, wx.ALL | wx.EXPAND, 5)
        left_sizer.Add(self.vol_slider_robot, 0, wx.ALL | wx.EXPAND, 5)
        left_sizer.Add(wx.StaticText(self.panel, label="App Volume"), 0, wx.ALL | wx.EXPAND, 5)
        left_sizer.Add(self.vol_slider_app, 0, wx.ALL | wx.EXPAND, 5)

        # Middle Section (Video Player and Transcript)
        middle_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Video Sizer
        video_sizer = wx.BoxSizer(wx.VERTICAL)
        video_sizer.Add(self.video_player, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER, 10)
        video_sizer.Add(self.switch_camera_button, 0, wx.ALL | wx.EXPAND, 5)

        middle_sizer.Add(left_sizer, 0, wx.ALL | wx.EXPAND, 10)
        middle_sizer.Add(video_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Right Section (Transcript)
        middle_sizer.Add(wx.StaticText(self.panel, label="Transcript:"), 0, wx.ALL | wx.EXPAND, 5)
        middle_sizer.Add(self.transcript_field, 0, wx.ALL | wx.EXPAND, 10)

        self.sizer.Add(middle_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Bottom Section (Arrow Buttons, Text to Speech)
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bottom_sizer.Add(self.rotate_right_button, 0, wx.ALL | wx.EXPAND, 5)
        bottom_sizer.Add(self.move_forward_button, 0, wx.ALL | wx.EXPAND, 5)
        bottom_sizer.Add(self.rotate_left_button, 0, wx.ALL | wx.EXPAND, 5)
        bottom_sizer.Add(self.sit_button, 0, wx.ALL | wx.EXPAND, 5)
        bottom_sizer.Add(self.stand_button, 0, wx.ALL | wx.EXPAND, 5)

        bottom_sizer.Add(wx.StaticText(self.panel, label="Text to speech:"), 0, wx.ALL | wx.EXPAND, 5)
        bottom_sizer.Add(self.tts_entry, 1, wx.ALL | wx.EXPAND, 5)
        bottom_sizer.Add(self.tts_button, 0, wx.ALL | wx.EXPAND, 5)        

        self.sizer.Add(bottom_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Bind events
        self.confirm_button.Bind(wx.EVT_BUTTON, self.process_input)
        self.disconnect_button.Bind(wx.EVT_BUTTON, self.disconnect_robot)
        
        self.sit_button.Bind(wx.EVT_BUTTON, lambda event: threading.Thread(target=self.relax_robot).start())
        self.stand_button.Bind(wx.EVT_BUTTON, lambda event: threading.Thread(target=self.wake_robot).start())

        self.switch_camera_button.Bind(wx.EVT_BUTTON, self.switch_camera)

        # Bind volume slider events
        self.vol_slider_robot.Bind(wx.EVT_SLIDER, self.volume_adjust_robot)
        self.vol_slider_app.Bind(wx.EVT_SLIDER, self.volume_adjust_app)

        # Bind events for button press
        self.move_forward_button.Bind(wx.EVT_LEFT_DOWN, lambda event: threading.Thread(target=self.move_forward).start())
        self.rotate_left_button.Bind(wx.EVT_LEFT_DOWN, lambda event: threading.Thread(target=self.rotate_left).start())
        self.rotate_right_button.Bind(wx.EVT_LEFT_DOWN, lambda event: threading.Thread(target=self.rotate_right).start())
        
        # Bind events for button release
        self.move_forward_button.Bind(wx.EVT_LEFT_UP, lambda event: threading.Thread(target=self.motion_stop).start())
        self.rotate_left_button.Bind(wx.EVT_LEFT_UP, lambda event: threading.Thread(target=self.motion_stop).start())
        self.rotate_right_button.Bind(wx.EVT_LEFT_UP, lambda event: threading.Thread(target=self.motion_stop).start())
                

        #self.close_button.Bind(wx.EVT_BUTTON, self.on_close)

        self.tts_button.Bind(wx.EVT_BUTTON, self.send_text)

    def on_key_down(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_LEFT:
            self.rotate_left(None)
        elif keycode == wx.WXK_RIGHT:
            self.rotate_right(None)
        elif keycode == wx.WXK_UP:
            self.move_forward(None)
        
    def process_input(self, event):
        """Checks for right IP and port entries, connects to given IP if passes"""
        if self.ip_entry.GetValue() == "":
            self.status.set("IP cannot be empty!")
        elif self.port_entry.GetValue() == "":
            self.status.set("PORT cannot be emtpy!")
        elif len(self.ip_entry.GetValue().split(".")) != 4:
            self.status.set("Invalid IP format!")
        elif not unicode(self.ip_entry.GetValue().replace(".", "")).isnumeric():
            self.status.set("IP can contain only numbers!")
        elif not unicode(self.port_entry.GetValue()).isnumeric():
            self.status.set("PORT can contain only numbers!")
        else:
            self.status.SetLabel("OK")
            self.status.Hide()
            #self.make_connect_file(self.ip_entry.GetValue(), self.port_entry.GetValue())
            self.connect(str(self.ip_entry.GetValue()), int(self.port_entry.GetValue()))

    def connect(self, NAO_ip, NAO_port):                    
        """Connect to robot, initiate variables and functions"""
        self.camera_index = 0
        self.MOVEMENT_SPEED = 0.6
        self.DETECTION_DIST = 1.5
        nao_ip = NAO_ip
        nao_port = (int)(NAO_port)

        self.broker = ALBroker("myBroker",
                          "0.0.0.0",  # listen to anyone
                          0,  # find a free port and use it
                          nao_ip,  # parent broker IP
                          nao_port)  # parent broker port
        self.motion = ALProxy("ALMotion", nao_ip, nao_port)  # movement stuff
        self.posture = ALProxy("ALRobotPosture", nao_ip, nao_port)  # posture - stand, sit etc
        self.tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)  # plain text to speech
        self.memory = ALProxy("ALMemory", nao_ip, nao_port)  # memory - everything there
        self.face_proxy = ALProxy("ALFaceDetection", nao_ip, nao_port)  # face detection etc
        self.camera = ALProxy("ALVideoDevice", nao_ip, nao_port)  # camera module
        self.audio = ALProxy("ALAudioDevice", nao_ip, nao_port)  # audio module
        self.tts_animated = ALProxy("ALAnimatedSpeech", nao_ip, nao_port)  # text to speech animated
        self.tts.setParameter("speed", 80)
        self.sonar = ALProxy("ALSonar", nao_ip, nao_port)  # sonar for distances
        # combination of all senses for zone detection
        self.people_perception = ALProxy("ALPeoplePerception", nao_ip, nao_port)
        engagement_zones = ALProxy("ALEngagementZones", nao_ip, nao_port)
        # lights on robot
        self.leds_light = ALProxy("ALLeds", nao_ip, nao_port)
        self.battery = ALProxy("ALBattery", nao_ip, nao_port)
        self.get_battery_charge()
        #self.robot_control_show()  # shows control portion of window

        # INITIALIZE FUNCTIONS
        # installed packages
        # print ALProxy("ALBehaviorManager", nao_ip, nao_port).getInstalledBehaviors()

        # 1 - Random  2 - Contextual animations
        self.tts_animated.setBodyLanguageMode(1)  # Animated Speech
        engagement_zones.setFirstLimitDistance(self.DETECTION_DIST)
        #init_facts()
        self.get_battery_charge()

        #global touch_reactor
        #self.touch_reactor = TouchReactor("touch_reactor")

        global ssh_client
        ssh_client = SSHClient(server=NAO_ip, username="nao", password="nao")
        ssh_client.connect()
        # Sets up LIVE robot audio stream
        ssh_client.run_ssh_command("gst-launch-0.10 pulsesrc ! audioconvert ! vorbisenc ! oggmux! tcpserversink port=1234")

        self.sound_streamer = self.SoundWorker("sound_streamer", "tcp://" + NAO_ip + ":1234")
        self.sound_streamer.start_stream()

        subscribers = self.camera.getSubscribers()
        for sub in subscribers:
            self.camera.unsubscribe(sub)
            print("found camera subscriber, unsubscribing")
        try:
            self.play_nao_video()
        except:
            print "Error getting video stream!"
            print traceback.format_exc()

        #check_for_visitor()
        self.get_battery_charge()
        print "CONNECTED"
        #self.robot_control_show()
        self.reset_pose("Crouch")
        self.LAST_POSE = "Crouch"

    def get_battery_charge(self):
        battery_charge = "N/A"
        try:
            battery_charge = str(self.battery.getBatteryCharge())
        except:
            print("Failed")
        self.battery_label_val.SetLabel(battery_charge)
        wx.CallLater(1000, self.get_battery_charge)
        
    def send_text(self, event):
        text_to_speak = self.tts_entry.GetValue()
        threading.Thread(target=self.tts_command, args=(text_to_speak,)).start()
        #print("Text to Speak:", text_to_speak)


    def volume_adjust_robot(self, event):
        """Changes volume of robot's output (loudspeakers)"""
        new_volume = self.vol_slider_robot.GetValue()
        self.audio.setOutputVolume(100-new_volume)
        self.robot_volume = new_volume
        

    def volume_adjust_app(self, event):
        """Adjusts robot input volume - what you hear on PC from robot microphone/s"""
        new_volume = self.vol_slider_app.GetValue()
        self.sound_streamer.change_volume(new_volume)
        self.app_volume = new_volume


    def disconnect_robot(self, event):
        """Disconnect robot connection"""
        robot_control_hide()
        status.set("Disconnected")


    def motion_stop(self):
        time.sleep(1)
        self.motion.stopMove()
        self.posture.goToPosture("Stand", self.MOVEMENT_SPEED)
 
        
    def move_forward(self):
        """Makes robot move forward a little bit"""
        self.motion.wakeUp()
        self.posture.goToPosture("Stand", self.MOVEMENT_SPEED)
        x = 0.8
        y = 0.0
        theta = 0.0
        frequency = 0.9
        self.motion.moveToward(x, y, theta, [["Frequency", frequency]])
        names = "HeadYaw"
        angles = 0.0
        fractionMaxSpeed = 0.1
        self.motion.setAngles(names, angles, fractionMaxSpeed)


    def rotate_left(self):
        self.motion.wakeUp()
        self.posture.goToPosture("Stand", self.MOVEMENT_SPEED)
        x = 0.0
        y = 0.0
        theta = 0.2
        frequency = 0.3
        self.motion.moveToward(x, y, theta, [["Frequency", frequency]])
        names = "HeadYaw"
        angles = 0.6
        fractionMaxSpeed = 0.1
        self.motion.setAngles(names, angles, fractionMaxSpeed)


    def rotate_right(self):
        self.motion.wakeUp()
        self.posture.goToPosture("Stand", self.MOVEMENT_SPEED)
        x = 0.0
        y = 0.0
        theta = -0.2
        frequency = 0.3
        self.motion.moveToward(x, y, theta, [["Frequency", frequency]])
        names = "HeadYaw"
        angles = -0.6
        fractionMaxSpeed = 0.1
        self.motion.setAngles(names, angles, fractionMaxSpeed)


    def switch_camera(self, event):
        if self.camera_index == 0:
            self.camera.setActiveCamera(1)
            self.camera_index = 1
        elif self.camera_index == 1:
            self.camera.setActiveCamera(0)
            self.camera_index = 0


    def change_head_angle():
        return
        # http://doc.aldebaran.com/2-4/naoqi/motion/control-joint.html


    def wake_robot(self):
        self.reset_pose("Stand")


    def relax_robot(self):
        self.reset_pose("Crouch")


    def reset_pose(self, pose):
        global LAST_POSE
        # taky lze rovnou pose do goToPosture misto pouzivani if
        if pose == "Stand":
            self.motion.wakeUp()
            self.posture.goToPosture("Stand", self.MOVEMENT_SPEED)
            self.LAST_POSE = "Stand"
        if pose == "Crouch":
            self.posture.goToPosture("Crouch", self.MOVEMENT_SPEED)
            self.motion.rest()
            self.LAST_POSE = "Crouch"


    def make_connect_file(ip, port):
        f = open("ip_port.txt", "w+")
        f.write(ip)
        f.write("\n")
        f.write(port)
        

if __name__ == "__main__":
    #wx.USE_BUFFERED_DC = True
    app = wx.App(False)
    frame = RobotControlFrame(None)
    frame.Show()
    app.MainLoop()
