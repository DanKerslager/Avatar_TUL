# Choregraphe bezier export in Python.
from naoqi import ALProxy
import unicodedata
names = list()
times = list()
keys = list()

names.append("HeadPitch")
times.append([0.16])
keys.append([[-0.169184, [3, -0.0666667, 0], [3, 0, 0]]])

# -*- coding: utf-8 -*-

text = u"""Dobrý den,
Já jsem Robot Nao
Vítejte na našem Blended Intensive program.

Tento program pro Vás připravila fakulta Mechatroniky, Informatiky a mezioborových studií.

Děkanem této fakulty je Josef Černohorský.

Potřebujete poradit s něčím ohledně organizace ? Obraťte se na naší koordinátorku Simonu Kuncovou.

Máme pro Vás připravené workshopy na téma:
 Brain Computer Interface
 Robot Operating Systém
 Digital Twin technology for offline robot programming
 Robotic assisted minimally invasive surgery

V rámci akce navštívíte i zajímavá místa mezi které patří Škoda Auto, Fakulta Biomedicínského
inženýrství ČVUT v Kladně. V rámci společného programu se setkáme i v místní kavárně Bez
Konceptu, kde pro Vás bude připravena večeře.
Celý program zakončíme společným výletem do Jizerských hor."""


try:
  # uncomment the following line and modify the IP if you use this script outside Choregraphe.
  # motion = ALProxy("ALMotion", IP, 9559)
  motion = ALProxy("ALMotion")
  speech = ALProxy("ALAnimatedSpeech")
  motion.angleInterpolationBezier(names, times, keys)
  speech.say(text.encode("utf-8"))
except BaseException as err:
  print(err) 
