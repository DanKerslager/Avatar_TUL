# -*- coding: utf-8 -*-
from naoqi import ALProxy
import unicodedata

text = u"""Dobry den,

Ja jsem Robot Nao a vitam vas na nasem Blended Intensive program.

Tento program pro Vas pripravila fakulta Mechatroniky, Informatiky a mezioborovych studii.

Dekanem teto fakulty je Josef Cernohorsky.

Potrebujete poradit s necim ohledne organizace ? Obratte se na nasi koordinatorku Simonu Kuncovou.

Chcete vice informaci o akci?"""

try:
    speech = ALProxy("ALTextToSpeech")
    speech.setLanguage("Czech")
    speech.setParameter("speed", 70)
    #speech.setParameter("pitch", 1.0)
    speechAnimated = ALProxy("ALAnimatedSpeech")
    speechAnimated.say(text.encode("utf-8"))
except BaseException as err:
  print(err) 
