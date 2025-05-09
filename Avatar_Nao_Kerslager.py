# -*- coding: utf-8 -*-
import threading
import wx
import os
import sys

from RobotControl import RobotControl
from JoystickWorker import JoystickPanel
from SttWorker import SttWorker

"""
PŘEDPOKLADY:
python 2.7(.18) (32bit!)
balíčky:

naoqi
    (https://community-static.aldebaran.com/resources/2.1.4.13/sdk-python/pynaoqi-2.1.4.13.win32.exe)
wx: "pip install wxpython==4.0.0.0"

extra: bind tlačítek na klávesnici pro ovládání robota (možná i přes ovladač?)
extra: nastavitelnost rychlosti pohybu - frekvence a krok - pomoci slidebarů
"""

thread = threading.Event()
process = None
api_key = 1

class RobotControlFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(RobotControlFrame, self).__init__(*args, **kw)
        self.SetSize((800, 600))
        self.SetTitle("Avatar Nao")
        self.ip_val = "192.168.0.122"
        self.port_val = "9559"
        self.robot_volume = 60
        self.app_volume = 60
        self.robot = None
        self.active = True
        self.language = "Czech"

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.timelines_folder = self.get_timelines_folder()
        self.timelines = self.get_timelines()
        self.timline_combo = wx.ComboBox(self.panel, choices=self.timelines, style=wx.CB_READONLY)
        self.load_timeline_button = wx.Button(self.panel, label="Load Timeline")

        # Initialize widgets
        self.status = wx.StaticText(self.panel, label="Status: Not Connected")
        self.sizer.Add(self.status, 0, wx.ALL | wx.EXPAND, 10)
        self.ip_entry = wx.TextCtrl(self.panel, value=self.ip_val)
        self.port_entry = wx.TextCtrl(self.panel, value=self.port_val)
        self.tts_entry = wx.TextCtrl(self.panel, value="Enter text to speak here..", size=(400, -1))

        self.confirm_button = wx.Button(self.panel, label="Connect")
        self.disconnect_button = wx.Button(self.panel, label="Disconnect/reset")
        self.sit_button = wx.Button(self.panel, label="Sit")
        self.stand_button = wx.Button(self.panel, label="Stand")

        self.move_forward_button = wx.Button(self.panel, label="^", size=(50, 50))
        self.rotate_left_button = wx.Button(self.panel, label="<", size=(50, 50))
        self.rotate_right_button = wx.Button(self.panel, label=">", size=(50, 50))

        self.switch_camera_button = wx.Button(self.panel, label="Switch Camera")
        self.tts_button = wx.Button(self.panel, label="Send text")
        # self.close_button = wx.Button(self.panel, label="Close")

        # Volume Sliders
        self.vol_slider_robot = wx.Slider(self.panel, value=self.robot_volume, minValue=0, maxValue=100,
                                          style=wx.SL_VERTICAL)
        self.vol_slider_app = wx.Slider(self.panel, value=self.app_volume, minValue=0, maxValue=100,
                                        style=wx.SL_VERTICAL)

        # Initialize video player
        self.video_player = wx.StaticBitmap(self.panel, size=(640, 480))
        self.video_player.SetBackgroundColour(wx.BLACK)

        # Initialize battery label
        self.battery_label = wx.StaticText(self.panel, label="Battery:")
        self.battery_label_val = wx.StaticText(self.panel, label="N/A")

        # Motion buttons
        self.pointer_left = wx.Button(self.panel, label="Point Left")
        self.pointer_front = wx.Button(self.panel, label="Point Front")
        self.pointer_right = wx.Button(self.panel, label="Point Right")
        self.waver = wx.Button(self.panel, label="Wave")

        self.joystick_panel = JoystickPanel(self.panel, self, self.move_head)

        self.new_window_button = wx.Button(self.panel, label="New window")
        self.active_toggle = wx.Button(self.panel, label="Active")
        self.voice_button = wx.Button(self.panel, label="Voice input: OFF")
        self.language_button = wx.Button(self.panel, label="CZ")

        self.Stt = SttWorker(self)

        self.create_widgets()
        self.bind_widgets()
        self.panel.SetSizer(self.sizer)
        self.sizer.Fit(self)

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
        top_sizer.Add(self.new_window_button, 0, wx.ALL | wx.EXPAND, 5)
        top_sizer.Add(self.active_toggle, 0, wx.ALL | wx.EXPAND, 5)
        top_sizer.Add(self.language_button, 0, wx.ALL | wx.EXPAND, 5)

        self.sizer.Add(top_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Left Section (Volume Sliders)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(wx.StaticText(self.panel, label="Robot Volume"), 0, wx.ALL | wx.EXPAND, 5)
        left_sizer.Add(self.vol_slider_robot, 0, wx.ALL | wx.EXPAND, 5)
        left_sizer.Add(wx.StaticText(self.panel, label="App Volume"), 0, wx.ALL | wx.EXPAND, 5)
        left_sizer.Add(self.vol_slider_app, 0, wx.ALL | wx.EXPAND, 5)

        # Middle Section (Video Player and Movement)
        middle_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Video Sizer
        video_sizer = wx.BoxSizer(wx.VERTICAL)
        video_sizer.Add(self.video_player, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER, 10)
        video_sizer.Add(self.switch_camera_button, 0, wx.ALL | wx.EXPAND, 5)

        middle_sizer.Add(left_sizer, 0, wx.ALL | wx.EXPAND, 10)
        middle_sizer.Add(video_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Right Section (Movement)
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        arrow_sizer = wx.BoxSizer(wx.HORIZONTAL)
        arrow_sizer.Add(self.rotate_left_button, 0, wx.ALL | wx.EXPAND, 5)
        arrow_sizer.Add(self.move_forward_button, 0, wx.ALL | wx.EXPAND, 5)
        arrow_sizer.Add(self.rotate_right_button, 0, wx.ALL | wx.EXPAND, 5)

        pose_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pose_sizer.Add(self.sit_button, 0, wx.ALL | wx.EXPAND, 5)
        pose_sizer.Add(self.stand_button, 0, wx.ALL | wx.EXPAND, 5)

        movement_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        movement_sizer1.Add(self.pointer_left, 0, wx.ALL | wx.EXPAND, 5)
        movement_sizer1.Add(self.pointer_right, 0, wx.ALL | wx.EXPAND, 5)

        movement_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        movement_sizer2.Add(self.pointer_front, 0, wx.ALL | wx.EXPAND, 5)
        movement_sizer2.Add(self.waver, 0, wx.ALL | wx.EXPAND, 5)


        timeline_sizer = wx.BoxSizer(wx.HORIZONTAL)
        timeline_sizer.Add(self.timline_combo, 0, wx.ALL | wx.EXPAND, 5)
        timeline_sizer.Add(self.load_timeline_button, 0, wx.ALL | wx.EXPAND, 5)

        joystick_sizer = wx.BoxSizer(wx.HORIZONTAL)
        joystick_sizer.Add(self.joystick_panel, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        right_sizer.Add(arrow_sizer, 0, wx.ALL | wx.EXPAND, 10)
        right_sizer.Add(pose_sizer, 0, wx.ALL | wx.EXPAND, 10)
        right_sizer.Add(movement_sizer1, 0, wx.ALL | wx.EXPAND, 10)
        right_sizer.Add(movement_sizer2, 0, wx.ALL | wx.EXPAND, 10)
        right_sizer.Add(timeline_sizer, 0, wx.ALL | wx.EXPAND, 10)
        right_sizer.Add(joystick_sizer, 0, wx.ALL | wx.EXPAND, 10)
        right_sizer.Add(self.voice_button, 0, wx.ALL | wx.EXPAND, 10)
        middle_sizer.Add(right_sizer, 0, wx.ALL | wx.EXPAND, 10)
        self.sizer.Add(middle_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Bottom Section 1 (Text to Speech)
        bottom_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        bottom_sizer1.Add(wx.StaticText(self.panel, label="Text to speech:"), 0, wx.ALL | wx.EXPAND, 5)
        bottom_sizer1.Add(self.tts_entry, 1, wx.ALL | wx.EXPAND, 5)
        bottom_sizer1.Add(self.tts_button, 0, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(bottom_sizer1, 0, wx.ALL | wx.EXPAND, 10)

    def bind_widgets(self):
        # Bind events
        self.confirm_button.Bind(wx.EVT_BUTTON, self.connect_robot)
        self.disconnect_button.Bind(wx.EVT_BUTTON, self.disconnect_robot)

        self.sit_button.Bind(wx.EVT_BUTTON,
                             lambda event: threading.Thread(target=self.go_pose, args=("Crouch",)).start())
        self.stand_button.Bind(wx.EVT_BUTTON,
                               lambda event: threading.Thread(target=self.go_pose, args=("Stand",)).start())

        self.switch_camera_button.Bind(wx.EVT_BUTTON, self.swap_camera)

        # Bind volume slider events
        self.vol_slider_robot.Bind(wx.EVT_SLIDER, self.volume_adjust_robot)
        self.vol_slider_app.Bind(wx.EVT_SLIDER, self.volume_adjust_app_event)

        # Bind events for button press
        self.move_forward_button.Bind(wx.EVT_LEFT_DOWN,
                                      lambda event: threading.Thread(target=self.move_forward).start())
        self.rotate_left_button.Bind(wx.EVT_LEFT_DOWN,
                                     lambda event: threading.Thread(target=self.rotate_left).start())
        self.rotate_right_button.Bind(wx.EVT_LEFT_DOWN,
                                      lambda event: threading.Thread(target=self.rotate_right).start())

        # Bind events for button release
        self.move_forward_button.Bind(wx.EVT_LEFT_UP,
                                      lambda event: threading.Thread(target=self.motion_stop).start())
        self.rotate_left_button.Bind(wx.EVT_LEFT_UP,
                                     lambda event: threading.Thread(target=self.motion_stop).start())
        self.rotate_right_button.Bind(wx.EVT_LEFT_UP,
                                      lambda event: threading.Thread(target=self.motion_stop).start())

        self.pointer_left.Bind(wx.EVT_BUTTON,
                               lambda event: threading.Thread(target=self.point_left).start())
        self.pointer_front.Bind(wx.EVT_BUTTON,
                                lambda event: threading.Thread(target=self.point_forward).start())
        self.pointer_right.Bind(wx.EVT_BUTTON,
                                lambda event: threading.Thread(target=self.point_right).start())
        self.waver.Bind(wx.EVT_BUTTON, lambda event: threading.Thread(target=self.wave).start())

        self.tts_button.Bind(wx.EVT_BUTTON, self.send_text)

        self.new_window_button.Bind(wx.EVT_BUTTON, init)

        self.active_toggle.Bind(wx.EVT_BUTTON, self.on_toggle)

        self.load_timeline_button.Bind(wx.EVT_BUTTON, self.on_load_timeline)

        self.voice_button.Bind(wx.EVT_BUTTON, self.voice_toggle)

        self.language_button.Bind(wx.EVT_BUTTON, self.swap_language)

    def connect_robot(self, event):
        """Checks for right IP and port entries, connects to given IP if passes"""
        if self.ip_entry.GetValue() == "":
            self.status.SetLabel("Status: IP cannot be empty!")
        elif self.port_entry.GetValue() == "":
            self.status.SetLabel("Status: PORT cannot be emtpy!")
        elif len(self.ip_entry.GetValue().split(".")) != 4:
            self.status.SetLabel("Status: Invalid IP format!")
        elif not unicode(self.ip_entry.GetValue().replace(".", "")).isnumeric():
            self.status.SetLabel("Status: IP can contain only numbers!")
        elif not unicode(self.port_entry.GetValue()).isnumeric():
            self.status.SetLabel("Status: PORT can contain only numbers!")
        else:
            self.robot = RobotControl(str(self.ip_entry.GetValue()), int(self.port_entry.GetValue()), self, self.timelines_folder)
            self.status.SetLabel("Status: Connected")

    def disconnect_robot(self, event=None):
        self.status.SetLabel("Status: Not Connected")
        self.robot.close()
        self.robot = None

    def on_close(self, event):
        # Perform cleanup tasks here
        self.Stt.Close()
        self.disconnect_robot()
        # Destroy the frame and exit the application
        self.Destroy()
        wx.GetApp().ExitMainLoop()

    def voice_toggle(self, event):
        if self.Stt.on:
            self.Stt.on = False
            self.voice_button.SetLabel("Voice input: OFF")
        else:
            self.Stt.on = True
            self.voice_button.SetLabel("Voice input: ON")

    def on_toggle(self, event):
        if self.active:
            self.active = False
            self.active_toggle.SetLabel("Inactive")
            self.volume_adjust_app(0)
            self.vol_slider_app.Disable()
            self.robot.movementWorker.motion.rest()
            self.robot.active(False)
        else:
            self.active = True
            self.active_toggle.SetLabel("Active")
            self.volume_adjust_app(self.app_volume)
            self.vol_slider_app.Enable()
            self.robot.active(True)

    def swap_language(self, event):
        if self.language == "Czech":
            self.language = "English"
            self.language_button.SetLabel("EN")
        else:
            self.language = "Czech"
            self.language_button.SetLabel("CZ")

    def send_text(self, event):
        value = self.tts_entry.GetValue()
        threading.Thread(target=self.robot.tts_command, args=(value,)).start()

    def get_timelines_folder(self):
        """Return the path to the 'timelines' folder, handling both script and executable cases."""
        if getattr(sys, 'frozen', False):  # Check if running from a bundled executable
            # Use the directory where the executable is located
            app_dir = os.path.dirname(sys.executable)
        else:
            # Use the directory of the current script in development
            app_dir = os.path.dirname(__file__)

        # Construct the path to the 'timelines' folder (relative to the exe or script)
        timelines_path = os.path.join(app_dir, 'timelines')
        return timelines_path

    def get_timelines(self):
        """Return a list of all Python files in the timelines folder."""
        timeline_files = []
        if os.path.exists(self.timelines_folder):
            for file in os.listdir(self.timelines_folder):
                # For simplicity, only include Python files (you can adjust the extension)
                if file.endswith('.py'):
                    timeline_files.append(file)
        return timeline_files
    
    def on_load_timeline(self, event):
        """Handle the event when the 'Load Timeline' button is clicked."""
        selected_timeline = self.timline_combo.GetValue()
        if selected_timeline:
            self.robot.timelines.play(selected_timeline)
        else:
            print("No timeline selected")

    def volume_adjust_robot(self, event):
        """Changes volume of robot's output (loudspeakers)"""
        self.robot.audio.setOutputVolume(100 - self.vol_slider_robot.GetValue())

    def volume_adjust_app_event(self, event):
        """Adjusts robot input volume - what you hear on PC from robot microphone/s"""
        val = self.vol_slider_app.GetValue()
        self.app_volume = val
        if self.active:
            self.volume_adjust_app(val)

    def volume_adjust_app(self, val):
        """Adjusts robot input volume - what you hear on PC from robot microphone/s"""
        self.robot.sound_streamer.change_volume(100-val)

    def swap_camera(self, event):
        self.robot.video.swap_camera()

    def move_forward(self):
        self.robot.movement.move_forward()

    def rotate_left(self):
        self.robot.movement.rotate_left()

    def rotate_right(self):
        self.robot.movement.rotate_right()

    def motion_stop(self):
        self.robot.movement.motion_stop()

    def go_pose(self, pose):
        self.robot.movement.go_pose(pose)

    def move_head(self, angle, tilt):
        self.robot.movement.move_head(-angle, tilt)

    def point_left(self):
        self.robot.movement.point_left()

    def point_right(self):
        self.robot.movement.point_right()

    def point_forward(self):
        self.robot.movement.point_forward()

    def wave(self):
        self.robot.movement.wave()


def init(event=None):
    # wx.USE_BUFFERED_DC = True
    app = wx.App(False)
    frame = RobotControlFrame(None)
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    init()
