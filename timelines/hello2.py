# -*- coding: utf-8 -*-
from naoqi import ALProxy
import unicodedata

text = u"""We have prepared workshops for you on the topic:

 Brain Computer Interface

 Robot Operating System

 Digital Twin technology for offline robot programming

 Robotic assisted minimally invasive surgery
"""

try:
    speech = ALProxy("ALTextToSpeech")
    speech.setLanguage("English")
    speech.setParameter("speed", 70)
    speechAnimated = ALProxy("ALAnimatedSpeech")
    speechAnimated.say(text.encode("utf-8"))
except BaseException as err:
    print(err)
