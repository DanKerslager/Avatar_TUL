import os
import sys
import threading
import re
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

    def replace_alproxy_calls(self, script):
        """
        Replace all ALProxy("ModuleName") with ALProxy("ModuleName", ip, port).
        """
        def replacer(match):
            module = match.group(1)
            return 'ALProxy("{}", "{}", {})'.format(module, self.robot_ip, self.robot_port)

        return re.sub(r'ALProxy\("([^"]+)"\)', replacer, script)

    def play(self, timeline_name):
        """
        Play a timeline exported from Choregraphe.
        
        :param timeline_name: Name of the timeline file (e.g., 'example_timeline.py').
        """
        self.running = True
        timeline_path = os.path.join(self.timeline_folder, timeline_name)

        # Check if the timeline file exists
        if not os.path.exists(timeline_path):
            print("Timeline file {timeline_name} not found in {self.timeline_folder}.")
            return
        
        with open(timeline_path, 'r') as file:
            script = file.read()
        
        # Apply substitutions
        script = self.replace_alproxy_calls(script)
        script = script.replace('BaseException, err:', 'BaseException as err:')
        script = script.replace('print err', 'print(err)')

        thread = threading.Thread(target=self.run_script_in_thread, args=(script, timeline_name))
        thread.start()

    def run_script_in_thread(self, script, timeline_name):
        try:
            exec(script, {"__name__": "__main__", "self": self})
            print("Successfully played timeline: {}".format(timeline_name))
        except Exception as e:
            print("Error executing timeline {}: {}".format(timeline_name, e))
        self.running = False


# Simple test for replacement logic
if __name__ == "__main__":
    dummy_script = '''
ALProxy("ALMotion")
ALProxy("ALTextToSpeech")
ALProxy("ALAnimatedSpeech")
'''
    with open("timelines/test.py", 'r') as file:
            script = file.read()
    class DummyWorker:
        robot_ip = "192.168.1.10"
        robot_port = 9559

    worker = TimelineWorker(timeline="", wxmain=None, robot_ip=DummyWorker.robot_ip, robot_port=DummyWorker.robot_port)
    replaced = worker.replace_alproxy_calls(script)
    print("Modified script:\n", replaced)
