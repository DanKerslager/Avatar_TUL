# -*- coding: utf-8 -*-
from naoqi import ALProxy
import unicodedata

text = u"""Mame pro Vas pripravene workshopy na tema: 
Brain Computer Interface 
Robot Operating System 
Digital Twin technology for offline robot programming 
Robotic assisted minimally invasive surgery 

V ramci akce navstivite i zajimava mista mezi ktere patri Skoda Auto, Fakulta Biomedicinskeho
inzenyrstvi CVUT v Kladne. V ramci spolecneho programu se setkame i v mistni kavarne Bez
Konceptu, kde pro Vas bude pripravena vecere.
Cely program zakoncime spolecnym vyletem do Jizerskych hor.

Pokud mate dalsi dotazy, rad Vam na ne odpovim."""

try:
    speech = ALProxy("ALTextToSpeech")
    speech.setLanguage("Czech")
    speech.setParameter("speed", 80)
    speechAnimated = ALProxy("ALAnimatedSpeech")
    speechAnimated.say(text.encode("utf-8"))
except BaseException as err:
    print(err)
