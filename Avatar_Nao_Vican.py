# -*- coding: utf-8 -*-
from Tkinter import *
import Tkinter as Tk
import tkMessageBox as messagebox
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


def init_facts():
    """List of facts for robot to speak, already spoken facts are to be moved from facts to used_facts to prevent
    same facts being spoken"""
    global used_facts, facts
    used_facts = []
    # possible upgrade: list of lists for different languages or dictionary for categories etc
    facts = [
        "Termín robot vychází z českého slova robota, jenž znamená dřina nebo nucená práce",
        "Roboti dělají pouze to, na co byli naprogramováni",
        "Asi polovina všech robotů na světě se vyskytuje v Asii, Japonsko jich má nejvíce se "
        "čtyřiceti procenty",
        "Robot ženského pohlaví se nazývá Gynoid nebo Fembot",  # https://en.wikipedia.org/wiki/Gynoid
        "Jsou 3 nejznámější pravidla pro roboty. Robot nesmí ublížit člověku. Musí poslouchat"
        "příkazy člověka pokud tím neporuší první pravidlo. Musí chránit svou existenci dokud tím "
        "neporuší první a druhé pravidlo"  # https://en.wikipedia.org/wiki/Three_Laws_of_Robotics
    ]


def reset_facts():
    for item in used_facts:
        facts.append(used_facts.pop(used_facts.index(item)))


def play_fact():
    """Play fact from list of facts and move it to used_facts, upon being empty will reset fact list"""
    if not facts:
        tts_animated.say("Už nemám žádné fakty co neznáte, budu vám povídat tedy ty předchozí")
        reset_facts()
        return
    leds_light.listGroup("FaceLeds")
    item = random.choice(facts)
    tts_animated.say(item)
    used_facts.append(facts.pop(facts.index(item)))
    reset_pose(LAST_POSE)

    # pops given item from facts and adds it to used_facts


def check_for_visitor():
    """Scans around robot and acts upon detecting objects/people"""
    # Sonicke senzory
    # left_sensor = memory.getData("Device/SubDeviceList/US/Left/Sensor/Value")
    # right_sensor = memory.getData("Device/SubDeviceList/US/Right/Sensor/Value")

    # if left_sensor > 0:
    #     print "Lsensoffr: ", left_sensor
    # if right_sensor > 0:
    #     print "Rsensor: ", right_sensor

    # mechanizmus na zjisteni osoby PRED robotem (do 1.5m)
    # TODO zmena detekcni vzdalenosti ruznych zon
    person_approach = memory.getData("EngagementZones/PeopleInZone1")
    person_far = memory.getData("EngagementZones/PeopleInZone2")
    if person_approach:
        print "Person close: ", person_approach
    if person_far:
        print "Person far: ", person_far

    app.after(3000, check_for_visitor)


def main(NAO_ip, NAO_port):
    """Connect to robot, initiate variables and functions"""
    global leds_light, sonar, motion, posture, tts, memory, audio
    global touch_reactor, people_perception, tts_animated, battery
    global broker, face_proxy, camera, camera_index
    global MOVEMENT_SPEED
    global LAST_POSE
    global DETECTION_DIST  # detection distance in front of robot
    MOVEMENT_SPEED = 0.6
    DETECTION_DIST = 1.5
    camera_index = 0  # sets which camera to use (0 - top, 1 - bottom)
    nao_ip = NAO_ip
    nao_port = (int)(NAO_port)

    broker = ALBroker("myBroker",
                      "0.0.0.0",  # listen to anyone
                      0,  # find a free port and use it
                      nao_ip,  # parent broker IP
                      nao_port)  # parent broker port
    motion = ALProxy("ALMotion", nao_ip, nao_port)  # movement stuff
    posture = ALProxy("ALRobotPosture", nao_ip, nao_port)  # posture - stand, sit etc
    tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)  # plain text to speech
    memory = ALProxy("ALMemory", nao_ip, nao_port)  # memory - everything there
    face_proxy = ALProxy("ALFaceDetection", nao_ip, nao_port)  # face detection etc
    camera = ALProxy("ALVideoDevice", nao_ip, nao_port)  # camera module
    audio = ALProxy("ALAudioDevice", nao_ip, nao_port)  # audio module
    tts_animated = ALProxy("ALAnimatedSpeech", nao_ip, nao_port)  # text to speech animated
    sonar = ALProxy("ALSonar", nao_ip, nao_port)  # sonar for distances
    # combination of all senses for zone detection
    people_perception = ALProxy("ALPeoplePerception", nao_ip, nao_port)
    engagement_zones = ALProxy("ALEngagementZones", nao_ip, nao_port)
    # lights on robot
    leds_light = ALProxy("ALLeds", nao_ip, nao_port)
    battery = ALProxy("ALBattery", nao_ip, nao_port)
    get_battery_charge()
    robot_control_show()  # shows control portion of window

    # INITIALIZE FUNCTIONS
    # installed packages
    # print ALProxy("ALBehaviorManager", nao_ip, nao_port).getInstalledBehaviors()

    # 1 - Random  2 - Contextual animations
    tts_animated.setBodyLanguageMode(1)  # Animated Speech
    engagement_zones.setFirstLimitDistance(DETECTION_DIST)
    init_facts()
    get_battery_charge()

    global touch_reactor
    touch_reactor = TouchReactor("touch_reactor")

    global ssh_client
    ssh_client = SSHClient(server=NAO_ip, username="nao", password="nao")
    ssh_client.connect()
    # Sets up LIVE robot audio stream
    ssh_client.run_ssh_command("gst-launch-0.10 pulsesrc ! audioconvert ! vorbisenc ! oggmux ! tcpserversink port=1234")

    global sound_streamer
    sound_streamer = SoundWorker("sound_streamer", "tcp://" + NAO_ip + ":1234")
    sound_streamer.start_stream()

    try:
        play_nao_video()
    except:
        print "Error getting video stream!"
        print traceback.format_exc()

    check_for_visitor()
    get_battery_charge()
    app.update_idletasks()
    print "CONNECTED"
    reset_pose("Crouch")
    LAST_POSE = "Crouch"


def get_battery_charge():
    try:
        battery_charge = battery.getBatteryCharge()
    except:
        battery_charge = "N/A"
    battery_charge_val.set(battery_charge)
    app.after(20000, get_battery_charge)


def play_nao_video(camera_index=0):
    """Subscribe to nao camera with given pamarameters"""
    # 2 - VGA. 11 - colorspace RGB
    # http://doc.aldebaran.com/2-1/family/robots/video_robot.html#cameracolorspace-mt9m114
    global video_client, process
    # time.sleep(1)
    video_client = camera.subscribe("_client", camera_index, 10, 25)
    # make new thread for streaming video
    show_video()


def show_video():
    """Get robot images and make video of them, also creates service call for it"""

    ### get image from robot
    # start = time.time()
    nao_image = camera.getImageRemote(video_client)

    # finish = time.time()
    # print "Odezva robota: ", finish - start
    # processing_time = time.time()
    # Get the image size and pixel array.
    image_width = nao_image[0]
    image_height = nao_image[1]
    array = nao_image[6]
    # Create a PIL Image from our pixel array.
    # pre-process for Tkinter
    # img = Image.fromarray(nao_image)
    img = Image.frombytes("YCbCr", (image_width, image_height), array)
    # cv2img = cv2.cvtColor()
    imgtk = ImageTk.PhotoImage(image=img)
    # video_player.image = imgTk
    processing_finished_time = time.time()
    # print "Odezva procesovani: ", processing_finished_time - processing_time
    video_player.imgtk = imgtk
    video_player.configure(image=imgtk)
    # repeat every 40ms
    video_player.after(20, show_video)


def process_commands(entry):
    """Process given commands and launch valid ones"""
    global LAST_POSE
    # posture.goToPosture("Stand", MOVEMENT_SPEED)
    invalid_counters = 0
    command_list = [
        "PCK",
        "PCK5",
        "OHL",
        "PL",
        "JED",
        "NMC",
        "PD",
        "OCK",
        "PZ"
    ]
    command_arr = entry.get().split()
    for command in command_arr:
        if command in command_list:
            play_command(command)
        else:
            invalid_counters += 1
    # posture.goToPosture("Stand", MOVEMENT_SPEED)
    num_invalid_commands.set(str(invalid_counters) + " Command/s were incompatible")
    reset_pose(LAST_POSE)
    print "Talking finished"


def play_command(command):
    if command == "PCK":
        print "PCK command"
        tts_animated.say("Prosím počkejte chvilku")
    if command == "PCK5":
        print "PCK 5 command"
        tts_animated.say("Prosím počkejte 5 minut")
    if command == "OHL":
        print "OHL command"
        tts_animated.say("hned vás ohlásím")
    if command == "PL":
        print "PL command"
        tts_animated.say("Pan Děkan")
    if command == "JED":
        print "JED command"
        tts_animated.say("Má zrovna jednání")
    if command == "NMC":
        print "NMC command"
        tts_animated.say("Zrovna nemá čas")
    if command == "PD":
        print "PD command"
        tts_animated.say("Pojďte dál prosím")
    if command == "OCK":
        print "OCK command"
        tts_animated.say("vás očekává")
    if command == "PZ":
        print "PZ command"
        tts_animated.say("Ahoj! ^start(animations/Stand/Gestures/Hey_1) "
                         "Rád vás vidím! ^wait(animations/Stand/Gestures/Hey_1)")
    # if command == "RUKA":
    #     print "potreseni rukou command"
    #     shake_hand()


def tts_command(entry):
    text = entry.get().encode("utf-8")
    tts_animated.say(text)
    reset_pose(LAST_POSE)


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


class SoundWorker(ALModule):
    def __init__(self, name, url):
        """Sets up media player"""
        ALModule.__init__(self, name)
        self.BIND_PYTHON(self.getName(), "callback")
        self.module_name = "SoundWorker"
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
        self.player.audio_set_volume(int(new_volume))


class TouchReactor(ALModule):
    """Handles anything related to robot touch"""

    def __init__(self, name):
        ALModule.__init__(self, name)
        # Subscribe to the TouchChanged event:
        xx = memory.subscribeToEvent("TouchChanged",
                                     "TouchReactor",
                                     "on_touch")
        print "TouchReactor: Subscribed"
        self.check_touch()

    def check_touch(self):
        """Checks for touch on robot bodies"""
        touch_data = memory.getData("TouchChanged")
        if len(touch_data) > 1:
            part = touch_data[0]
            part_bool = part[1]
            part_specific = touch_data[1]
            part_specific_bool = part_specific[1]
            # print touch_data
            if touch_data:
                self.on_touch(part_specific[0], touch_data)
        app.after(1300, self.check_touch)

    def on_touch(self, part_name, value, number=None):
        """Checks what part of body has been touched then reacts to it (if needed)"""
        # vypnuti opetovne reakce na stisk
        memory.unsubscribeToEvent("TouchChanged", "TouchReactor")
        touched_bodies = []
        # print "Detecting touch..."
        for touched in value:  # true/false hodnot pokud byli stisknuty
            if touched[1]:
                print touched_bodies
                touched_bodies.append(part_name)
        # print touched_bodies
        if "Head/Touch/Rear" in touched_bodies:
            threading.Thread(target=play_fact(), args=(thread,)).start()

        memory.subscribeToEvent("TouchChanged", "TouchReactor", "on_touch")


def gui():
    """Creates and configures the UI of the application"""
    global ip
    global port
    global status, num_invalid_commands, video_player, robot_volume, app_volume, battery_charge_val
    global app
    ip_val = "192.168.0.120"
    port_val = "9559"


    robot_volume = 60
    app_volume = 60

    try:
        file = open("ip_port.txt", "r+")
        data = file.read().splitlines()
        ip_val = str(data[0])
        port_val = str(data[1])
    except Exception:
        print "Unable to read file to load parameters, using default ones"
    try:
        file = open("sound_config.txt", "r+")
        data = file.read().splitlines()
        robot_volume = str(data[0])
        app_volume = str(data[1])
    except Exception:
        print "Unable to read file to load sound parameters, using default ones"

    app = Tk.Tk()

    bigger_font = tkFont.Font(root=app, size=15)
    app.title("Sekretářka Nao")
    grid_config()  # sets up grid of window
    # TODO - až bude hotovo odkomentovat
    # app.protocol("WM_DELETE_WINDOW", on_close)

    # ip textbox
    ip = StringVar(value=ip_val)
    ip_label = Label(app, text="IP:")
    ip_entry = Entry(app, width=0, textvariable=ip)

    # port textbox
    port = StringVar(value=port_val)
    port_label = Label(app, text="PORT:")
    port_entry = Entry(app, width=0, textvariable=port)

    # command textbox
    command = StringVar(value="Enter commands here.. ")
    command_label = Label(app, text="Commands: ")
    command_entry = Entry(app, width=50, textvariable=command)
    command_button = Button(master=app, text="Send Command",
                            command=lambda: threading.Thread(target=process_commands(command)).start())

    # buttons
    confirm_button = Button(master=app, text="Connect", command=process_input)
    disconnect_button = Button(master=app, text="Disconnect/reset", command=disconnect_robot)
    sit_button = Button(master=app, text="Sit",
                        command=lambda: threading.Thread(target=relax_robot).start(), width=5)
    stand_button = Button(master=app, text="Stand",
                          command=lambda: threading.Thread(target=wake_robot).start(), width=5)

    move_forward_button = Button(master=app, text="^", font=bigger_font)
    rotate_left_button = Button(master=app, text="<", font=bigger_font)
    rotate_right_button = Button(master=app, text=">", font=bigger_font)

    switch_camera_button = Button(master=app, text="Switch Camera",
                                  command=lambda: threading.Thread(target=switch_camera).start())

    # bind to arrow keys
    move_forward_button.bind("<KeyPress-Up>", move_forward)
    rotate_right_button.bind("<KeyPress-Right>", rotate_right)
    rotate_left_button.bind("<KeyPress-Left>", rotate_left)

    move_forward_button.bind("<KeyRelease-Up>", motion_stop)
    rotate_right_button.bind("<KeyRelease-Right>", motion_stop)
    rotate_left_button.bind("<KeyRelease-Left>", motion_stop)

    # bind buttons for continuous execution
    move_forward_button.bind("<ButtonPress>", move_forward)
    rotate_right_button.bind("<ButtonPress>", rotate_right)
    rotate_left_button.bind("<ButtonPress>", rotate_left)

    # on release stop all movement
    move_forward_button.bind("<ButtonRelease>", motion_stop)
    rotate_right_button.bind("<ButtonRelease>", motion_stop)
    rotate_left_button.bind("<ButtonRelease>", motion_stop)

    # Text to speech setup
    tts_var = StringVar(value="Enter text to speak here..")
    tts_label = Label(app, text="Text to speech:")
    tts_entry = Entry(app, width=50, textvariable=tts_var)
    tts_button = Button(master=app, text="Send text",
                        command=lambda: threading.Thread(target=tts_command(tts_var)).start())

    # status label
    status = StringVar(value="Status:")
    status_label = Label(app, text="", textvariable=status)

    video_player = Label(master=app)
    num_invalid_commands = StringVar(value="")
    commands_worked = Label(app, text="", textvariable=num_invalid_commands)
    battery_charge_val = StringVar(value="N/A")
    battery_charge_label = Label(app, text="Battery charge:")
    battery_charge_label_val = Label(app, text="", textvariable=battery_charge_val)

    vol_slider_robot = Scale(app, label="Robot volume", orient=Tk.HORIZONTAL,
                             command=volume_adjust_robot)
    vol_slider_app = Scale(app, label="App volume", orient=Tk.HORIZONTAL,
                           command=volume_adjust_app, to=200)

    # key bindings
    ip_entry.bind("<Return>", lambda event=None: threading.Thread(target=confirm_button.invoke()).start())
    command_entry.bind("<Return>", lambda event=None: threading.Thread(target=command_button.invoke()).start())
    port_entry.bind("<Return>", lambda event=None: threading.Thread(target=confirm_button.invoke()).start())
    tts_entry.bind("<Return>", lambda event=None: threading.Thread(target=tts_command.invoke()).start())

    vol_slider_robot.grid(in_=app, column=2, row=8, columnspan=1, rowspan=1, sticky="e")
    vol_slider_app.grid(in_=app, column=2, row=9, columnspan=1, rowspan=1, sticky="s")
    vol_slider_robot.set(robot_volume)
    vol_slider_app.set(app_volume)

    # buttons
    disconnect_button.grid(in_=app, column=4, row=4, columnspan=1, padx=15)
    confirm_button.grid(in_=app, column=5, row=4, columnspan=1, rowspan=1)
    command_button.grid(in_=app, column=5, row=5, columnspan=1, rowspan=1, ipadx=0, ipady=10, padx=10, sticky="ew")
    sit_button.grid(in_=app, column=5, row=8, columnspan=1, rowspan=1, sticky="e")
    stand_button.grid(in_=app, column=5, row=8, columnspan=1, rowspan=1, sticky="w")
    tts_button.grid(in_=app, column=5, row=7, columnspan=1, rowspan=1, ipadx=0, ipady=10, padx=10, sticky="ew")
    move_forward_button.grid(in_=app, column=3, row=8, columnspan=2, rowspan=1)
    rotate_left_button.grid(in_=app, column=3, row=9, columnspan=1, rowspan=1, sticky="e")
    rotate_right_button.grid(in_=app, column=4, row=9, columnspan=1, rowspan=1)
    switch_camera_button.grid(in_=app, column=2, row=10, columnspan=1, rowspan=1)

    # labels
    ip_label.grid(in_=app, column=2, row=2, columnspan=1, rowspan=1, sticky="nsew")
    port_label.grid(in_=app, column=4, row=2, columnspan=1, rowspan=1, sticky="nsew")
    status_label.grid(in_=app, column=3, row=1, columnspan=6, rowspan=1, sticky="nsew")
    command_label.grid(in_=app, column=2, row=5, columnspan=1, rowspan=1, sticky="e")
    tts_label.grid(in_=app, column=2, row=7, columnspan=1, rowspan=1, sticky="e")
    video_player.grid(in_=app, column=2, row=11, columnspan=4, rowspan=4, sticky="nsew")
    commands_worked.grid(in_=app, column=3, row=6, columnspan=2, rowspan=1)
    battery_charge_label.grid(in_=app, column=5, row=9, rowspan=1, columnspan=1)
    battery_charge_label_val.grid(in_=app, column=5, row=10, rowspan=1, columnspan=1, sticky="n")


    # entry fields
    ip_entry.grid(in_=app, column=3, row=2, columnspan=1, sticky="nsew")
    port_entry.grid(in_=app, column=5, row=2, columnspan=1, rowspan=1, sticky="nsew")
    command_entry.grid(in_=app, column=3, row=5, columnspan=2, rowspan=1, sticky="e")
    tts_entry.grid(in_=app, column=3, row=7, columnspan=2, rowspan=1, sticky="e")

    # command labels (options for command entries)
    text_bold = tkFont.Font(family="Helvetica", weight="bold", size=10)
    cmd_heading = Label(app, text="Executable commands:", font=text_bold)

    cmd_1 = Label(app, text="PCK    PCK5")
    cmd_2 = Label(app, text="OHL    PL")
    cmd_3 = Label(app, text="JED    NMC")
    cmd_4 = Label(app, text="PD     OCK")
    cmd_5 = Label(app, text="PZ")

    cmd_heading.grid(in_=app, column=9, row=4, columnspan=1, rowspan=2, sticky="w")
    cmd_1.grid(in_=app, column=9, row=5, columnspan=1, rowspan=1, sticky="w")
    cmd_2.grid(in_=app, column=9, row=6, columnspan=1, rowspan=1, sticky="w")
    cmd_3.grid(in_=app, column=9, row=7, columnspan=1, rowspan=1, sticky="w")
    cmd_4.grid(in_=app, column=9, row=8, columnspan=1, rowspan=1, sticky="nw")
    cmd_5.grid(in_=app, column=9, row=8, columnspan=1, rowspan=1, sticky="sw")

    

    


    app.resizable(False, False)

    robot_control_hide() # hides conntrol panel until robot is coonnected
    app.mainloop()


def grid_config():
    """Sets up grid to stick widgets to in app"""
    app.grid_rowconfigure(1, weight=30, minsize=16)
    app.grid_rowconfigure(2, weight=15, pad=0)
    app.grid_rowconfigure(3, weight=40, pad=0)

    app.grid_rowconfigure(4, weight=20, pad=15)
    app.grid_rowconfigure(5, weight=20, pad=0)
    app.grid_rowconfigure(6, weight=20, pad=0)
    app.grid_rowconfigure(7, weight=20, pad=0)
    app.grid_rowconfigure(8, weight=20, pad=0)
    app.grid_rowconfigure(9, weight=20, pad=0)

    app.grid_rowconfigure(10, weight=200, pad=0)
    app.grid_rowconfigure(11, weight=200, pad=0)
    app.grid_rowconfigure(12, weight=200, pad=0)

    app.grid_columnconfigure(1, weight=10, pad=0)
    app.grid_columnconfigure(2, weight=20, pad=0)
    app.grid_columnconfigure(3, weight=30, pad=0)
    app.grid_columnconfigure(4, weight=50, pad=0)
    app.grid_columnconfigure(5, weight=100, pad=0)
    app.grid_columnconfigure(6, weight=16, pad=0)
    app.grid_columnconfigure(7, weight=16, minsize=16, pad=0)
    app.grid_columnconfigure(8, weight=20, minsize=20, pad=0)
    app.grid_columnconfigure(9, weight=50, minsize=30, pad=10)


def robot_control_hide():
    """Hides widgets for controlling the robot"""
    widgets = app.winfo_children()
    # print widgets.__sizeof__()
    for widget in widgets:
        widget.grid_info()
        if int(widget.grid_info()["row"]) > 4 or (int(widget.grid_info()["row"]) == 4 and int(widget.grid_info()["column"]) == 9):
            widget.grid_remove()


def robot_control_show():
    """Shows widgets for controlling the robot"""
    widgets = app.winfo_children()
    # print widgets.__sizeof__()
    for widget in widgets:
        widget.grid()


def volume_adjust_robot(new_volume):
    """Changes volume of robot's output (loudspeakers)"""
    # print "New ROBOT volume!", new_volume
    audio.setOutputVolume(int(new_volume))
    global robot_volume
    robot_volume = int(new_volume)
    make_sound_config_file("sound_config", robot_volume, app_volume)


def volume_adjust_app(new_volume):
    """Adjusts robot input volume - what you hear on PC from robot microphone/s"""
    # print "New APP volume!", new_volume
    global app_volume
    app_volume = int(new_volume)
    sound_streamer.change_volume(new_volume)
    make_sound_config_file("sound_config", robot_volume, app_volume)


def disconnect_robot():
    """Disconnect robot connection"""
    robot_control_hide()
    status.set("Disconnected")


def motion_stop(event):
    motion.stopMove()
    posture.goToPosture("Stand", MOVEMENT_SPEED)


def move_forward(event):
    """Makes robot move forward a little bit"""
    motion.wakeUp()
    posture.goToPosture("Stand", MOVEMENT_SPEED)
    x = 0.8
    y = 0.0
    theta = 0.0
    frequency = 0.9
    motion.moveToward(x, y, theta, [["Frequency", frequency]])
    names = "HeadYaw"
    angles = 0.0
    fractionMaxSpeed = 0.1
    motion.setAngles(names, angles, fractionMaxSpeed)


def rotate_left(event):
    motion.wakeUp()
    posture.goToPosture("Stand", MOVEMENT_SPEED)
    x = 0.0
    y = 0.0
    theta = 0.2
    frequency = 0.3
    motion.moveToward(x, y, theta, [["Frequency", frequency]])
    names = "HeadYaw"
    angles = 0.6
    fractionMaxSpeed = 0.1
    motion.setAngles(names, angles, fractionMaxSpeed)


def rotate_right(event):
    motion.wakeUp()
    posture.goToPosture("Stand", MOVEMENT_SPEED)
    x = 0.0
    y = 0.0
    theta = -0.2
    frequency = 0.3
    motion.moveToward(x, y, theta, [["Frequency", frequency]])
    names = "HeadYaw"
    angles = -0.6
    fractionMaxSpeed = 0.1
    motion.setAngles(names, angles, fractionMaxSpeed)


def switch_camera():
    global camera_index
    if camera_index == 0:
        camera.setActiveCamera(1)
        camera_index = 1
    elif camera_index == 1:
        camera.setActiveCamera(0)
        camera_index = 0


def change_head_angle():
    return
    # http://doc.aldebaran.com/2-4/naoqi/motion/control-joint.html


def wake_robot():
    reset_pose("Stand")


def relax_robot():
    reset_pose("Crouch")


def reset_pose(pose):
    global LAST_POSE
    # taky lze rovnou pose do goToPosture misto pouzivani if
    if pose == "Stand":
        motion.wakeUp()
        posture.goToPosture("Stand", MOVEMENT_SPEED)
        LAST_POSE = "Stand"
    if pose == "Crouch":
        posture.goToPosture("Crouch", MOVEMENT_SPEED)
        motion.rest()
        LAST_POSE = "Crouch"


def process_input(event):
    """Checks for right IP and port entries, connects to given IP if passes"""
    if ip.get() in "":
        status.set("IP cannot be empty!")
    elif port.get() in "":
        status.set("PORT cannot be emtpy!")
    elif len(ip.get().split(".")) != 4:
        status.set("Invalid IP format!")
    elif not unicode(ip.get().replace(".", "")).isnumeric():
        status.set("IP can contain only numbers!")
    elif not unicode(port.get()).isnumeric():
        status.set("PORT can contain only numbers!")
    else:
        status.set("OK")
        make_connect_file(ip.get(), port.get())
        main(ip.get(), port.get())


def make_connect_file(ip, port):
    f = open("ip_port.txt", "w+")
    f.write(ip)
    f.write("\n")
    f.write(port)


def make_sound_config_file(filename, robot_volume, app_volume):
    f = open(filename + ".txt", "w+")
    f.write(str(robot_volume))
    f.write("\n")
    f.write(str(app_volume))


def on_close():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        app.destroy()


if __name__ == '__main__':
    gui()
