# -*- coding: utf-8 -*-
from naoqi import ALProxy
import unicodedata

text = u"""We have prepared workshops for you on the topic:

 Brain Computer Interface

 Robot Operating System

 Digital Twin technology for offline robot programming

 Robotic assisted minimally invasive surgery

As part of the event, you will also visit interesting places, including Skoda Auto, the Faculty of
Biomedical Engineering of the Czech Technical University in Kladno. As part of the joint program, we
will also meet at the local cafe Bez Konceptu, where dinner will be prepared for you.
We will end the entire program with a joint trip to the Jizera Mountains.

If you have any further questions, I will be happy to answer them."""

try:
    speech = ALProxy("ALTextToSpeech")
    speech.setLanguage("English")
    speech.setParameter("speed", 70)
    speechAnimated = ALProxy("ALAnimatedSpeech")
    speechAnimated.say(text.encode("utf-8"))
except BaseException as err:
    print(err)
