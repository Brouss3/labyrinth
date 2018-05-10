Goals: 
======

* It's a game POC. Labyrinth grinder in simple 3D viewing a la doom.
* Programmed in python3, using no additionnal library
* You can have fun with it for a few minuts.
* Only one map proposed... It's just a POC

Usage:
======
    
* ./labyrinth.pi

Ingame Keys:
============

* arrows	Navigate
* A/Z		Change zoom level
* P		PrintScreen (to lab.screenshot.txt)
* Q		Quit

Important Notices:
==================

* Labyrinth.py fiddles with curses. This could disrupt your bash session
display with: unreadable output, messed CRLF, no keyboard echo. In such a
case, you need to kill your console and start a new one. DO NOT run
labyrinth.py on a console you NEED to work from afterward.
* Labyrinth.py also fiddles with keyboard repetition latency settings for 
smoother navigation. This affects ALL YOUR SYSTEM and will have undesired 
effects if you work on another program while having a labyrinth.py running.
* Labyrinth.py resets keyboard latency setting to default afterward. If for 
some reason your box does not use default keyboard, DO NOT run labyrinth.py
on this box. 
* If for some reason Labyrinth.py did not give you back the default keyboard
latency setting, please copy and paste the following instruction in a bash
session to reset:

> xset r rate 660 25 

