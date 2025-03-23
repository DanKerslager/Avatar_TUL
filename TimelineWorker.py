import os
import sys
from naoqi import ALProxy

class TimelineWorker:
    """
    A class to manage and play Choregraphe-exported timelines.
    """
    
    def __init__(self, timeline, wxmain, robot_ip, robot_port=9559):
        """
        Initialize the TimelinePlayer with the NAO robot's connection details.
        
        :param robot_ip: IP address of the NAO robot.
        :param robot_port: Port of the NAO robot (default: 9559).
        """
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.timeline_folder = timeline
        self.wxmain = wxmain
        self.running = False


    def play(self, timeline_name):
        """
        Play a timeline exported from Choregraphe.
        
        :param timeline_name: Name of the timeline file (e.g., 'example_timeline.py').
        """
        self.running = True
        # Combine timeline folder path with the timeline file name
        timeline_path = os.path.join(self.timeline_folder, timeline_name)

        # Check if the timeline file exists
        if not os.path.exists(timeline_path):
            print("Timeline file {timeline_name} not found in {self.timeline_folder}.")
            return
        
        # Read the timeline script
        with open(timeline_path, 'r') as file:
            script = file.read()
        
        # Replace the placeholder ALProxy with actual robot IP and port
        script = script.replace('ALProxy("ALMotion")', 'ALProxy("ALMotion", "{self.robot_ip}", {self.robot_port})')
        script = script.replace('BaseException, err:', 'BaseException as err:')
        script = script.replace('print err', 'print(err)')

        # Execute the script safely
        try:
            exec(script, {"__name__": "__main__", "ALProxy": ALProxy})
            print("Successfully played timeline: {timeline_name}")
        except Exception as e:
            print("Error executing timeline {timeline_name}: {e}")
        self.running = False

