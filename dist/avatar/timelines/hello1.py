# -*- coding: utf-8 -*-
from naoqi import ALProxy
import unicodedata

text = u"""Hello,
I am Robot Nao
Welcome to our Blended Intensive program.

This program has been prepared for you by the Faculty of Mechatronics, Informatics and
Interdisciplinary Studies.

The Dean of this faculty is Josef Cernohorsky.

Do you need advice on something regarding the organization? Contact our coordinator Simona Kuncova.

Shall I give you more information about the event?"""

try:
    speech = ALProxy("ALTextToSpeech")
    speech.setLanguage("English")
    speech.setParameter("speed", 70)
    speechAnimated = ALProxy("ALAnimatedSpeech")
    speechAnimated.say(text.encode("utf-8"))
except BaseException as err:
    print(err)
