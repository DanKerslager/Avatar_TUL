# -*- coding: utf-8 -*-
from naoqi import ALProxy
import unicodedata

text = u"""Vložte text, který chcete, aby robot přečetl. 
        Insert the text you want the robot to read."""

# Pro kombinaci s exportovanou pohybovou timeline do ní doplňte kód z tohoto souboru.
# For combination with the exported motion timeline, add the code from this file to it.

try:
    speech = ALProxy("ALTextToSpeech")
    speech.setLanguage("Czech") # Set the language "English" or "Czech"
    speech.setParameter("speed", 70)
    #speech.setParameter("pitch", 1.0)
    speechAnimated = ALProxy("ALAnimatedSpeech")
    speechAnimated.say(text.encode("utf-8"))
except BaseException as err:
  print(err) 
