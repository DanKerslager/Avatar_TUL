from naoqi import ALProxy
import time
import threading

class MovementWorker:
    def __init__(self, wxmain, nao_ip, nao_port):
        self.wxmain = wxmain
        self.MOVEMENT_SPEED = 0.6
        self.motion = ALProxy("ALMotion", nao_ip, nao_port)  # movement stuff
        self.posture = ALProxy("ALRobotPosture", nao_ip, nao_port)  # posture - stand, sit etc
        self.motion.wbEnable(True)
        self.pose = "Crouch"
        self.life = ALProxy("ALAutonomousLife", nao_ip, nao_port)

    def go_pose(self, pose):
        self.motion.wakeUp()
        threading.Thread(target=self.posture.goToPosture, args=(pose, self.MOVEMENT_SPEED)).start()
        self.pose = pose
        time.sleep(2)
        self.life.setState("disabled")
        if (self.pose =="Crouch"):
            self.rest()
        elif (self.pose == "Stand"):
            self.life.setState("solitary")

    def rest(self):
        self.motion.rest()

    def reset_pose(self):
        self.go_pose(self.pose)


    def move_forward(self):
        """Makes robot move forward a little bit"""
        self.motion.wakeUp()
        self.posture.goToPosture("StandInit", self.MOVEMENT_SPEED)
        x = 0.8
        y = 0.0
        theta = 0.0
        frequency = 0.9
        self.motion.moveToward(x, y, theta, [["Frequency", frequency]])
        names = "HeadYaw"
        angles = 0.0
        fraction_max_speed = 0.1
        self.motion.setAngles(names, angles, fraction_max_speed)
        self.reset_pose()

    def rotate_left(self):
        self.motion.wakeUp()
        self.posture.goToPosture("StandInit", self.MOVEMENT_SPEED)
        x = 0.0
        y = 0.0
        theta = 0.2
        frequency = 0.3
        self.motion.moveToward(x, y, theta, [["Frequency", frequency]])
        names = "HeadYaw"
        angles = 0.6
        fraction_max_speed = 0.1
        self.motion.setAngles(names, angles, fraction_max_speed)
        self.reset_pose()

    def rotate_right(self):
        self.motion.wakeUp()
        self.posture.goToPosture("StandInit", self.MOVEMENT_SPEED)
        x = 0.0
        y = 0.0
        theta = -0.2
        frequency = 0.3
        self.motion.moveToward(x, y, theta, [["Frequency", frequency]])
        names = "HeadYaw"
        angles = -0.6
        fraction_max_speed = 0.1
        self.motion.setAngles(names, angles, fraction_max_speed)
        self.reset_pose()

    def motion_stop(self):
        time.sleep(1)
        self.motion.stopMove()
        self.posture.goToPosture("Stand", self.MOVEMENT_SPEED)

    def point_left(self):
        # Extend the left arm towards the robot's left
        self.motion.angleInterpolation(
            ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll"],
            [0, 2, 0, 0],  # Angles for pointing left
            [1.0, 1.0, 1.0, 1.0],  # Duration in seconds for each joint
            True  # Move all joints simultaneously
        )
        self.reset_pose()

    def point_right(self):
        # Extend the right arm towards the robot's right
        self.motion.angleInterpolation(
            ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll"],
            [0, -2, 0, 0],  # Angles for pointing right
            [1.0, 1.0, 1.0, 1.0],  # Duration in seconds for each joint
            True  # Move all joints simultaneously
        )
        self.reset_pose()

    def point_forward(self):
        # Both arms extended forward
        self.motion.angleInterpolation(
            [
             "RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll"],
            [0.0, 0.0, 0.0, 0.5],  # Right arm angles
            [1.0, 1.0, 1.0, 1.0],  # Duration for each joint
            True  # Move all joints simultaneously
        )
        self.reset_pose()

    def wave(self):
        # Perform a wave with the right arm
        names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw"]
        # Sequence of angles for the waving motion
        angleLists = [
            [0, 0, 0, 0, 0, 0],  # RShoulderPitch
            [-1, -1, -1, -1, -1, -1],  # RShoulderRoll
            [1.5, 1.0, 1.5, 1.0, 1.5, 1.0],  # RElbowYaw
            [1.5, 0.0, 1.5, 0.0, 1.5, 0.0],  # RElbowRoll
            [0.0, 0.5, 0.0, 0.5, 0.0, 0.5]  # RWristYaw
        ]
        # Time for each angle change in seconds
        timeLists = [[1.0, 1.5, 2.0, 2.5, 3.0, 3.5] for _ in range(len(names))]
        self.motion.angleInterpolation(names, angleLists, timeLists, True)
        self.reset_pose()

    def move_head(self, angle, tilt):
        names = ["HeadYaw", "HeadPitch"]
        angles = [angle, tilt]
        self.motion.setAngles(names, angles, 0.2)

    def head_update(self):
        pass
