# -*- coding: utf-8 -*-
from naoqi import ALProxy
import unicodedata

text = u"""Hello, how was the seminar?

I hope you will enjoy the Blended intensive program.

Automatic coffee machine can be found one floor below, or i can recommend coffee shop Bez konceptu, which can be found on the university square."""

try:
    print("playing timeline hello3")
    speech = ALProxy("ALTextToSpeech")
    speech.setLanguage("English")
    speech.setParameter("speed", 70)
    speechAnimated = ALProxy("ALAnimatedSpeech")
    speechAnimated.say(text.encode("utf-8"))
except BaseException as err:
    print(err)
