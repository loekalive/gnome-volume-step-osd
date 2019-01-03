#!/usr/bin/python3
# By: Garrett Holbrook
# Date: August 27th, 2015
#
# Usage: Changes the system volume through amixer and then 
#        makes a dbus method call to the gnome shell to get the
#        gnome volume OSD (On Screen Display)
#
# Requires: python3 and python-dbus (on Arch) or python3-dbus
#           (on Debian) or equivalent
from dbus import Interface, SessionBus
from re import findall, search
from sys import argv, exit
from subprocess import check_output

# Set any amixer options we need. Adjust if the default doesn't work for you.
# base_cmd = ['amixer', '-D', 'pulse']
# base_cmd = ['amixer', '-D', 'alsa']
base_cmd = ['amixer']
volume_type = 'Master'

# Interpreting how to affect the volume and by what percentage
vol_action = argv[1]
if vol_action in ['increase', 'decrease']:
    vol_percent_change = int(argv[2])
elif vol_action in ['mute']:
    vol_percent_change = 0
else:
    print("ERROR: command not one of 'decrease', 'increase' or 'mute': {}".format(vol_action))
    exit(1)

# Getting the dbus interface to communicate with gnome's OSD
session_bus = SessionBus()
proxy = session_bus.get_object('org.gnome.Shell', '/org/gnome/Shell')
interface = Interface(proxy, 'org.gnome.Shell')

# Get the current state.
output = check_output(base_cmd + ['sget', volume_type]).decode('utf-8')

# Mute status.
try:
    on = search(r'\[(on)?(off)?\]', output).group(1)
except IndexError:
    print("ERROR: no volume information found, try changing base_cmd")
    exit(1)

# Calculate the new level based on an average for all levels.
vol_percentage = [int(x) for x in findall(r'\[(\d{1,3})\%\]', output)]
vol_percentage = int(sum(vol_percentage)/len(vol_percentage)+0.5)
if vol_action == 'increase':
    vol_percentage += vol_percent_change
elif vol_action == 'decrease':
    vol_percentage -= vol_percent_change
if vol_percentage > 100:
    vol_percentage = 100
label = "{}%".format(vol_percentage)

# Make actual changes.
if vol_action in ['increase', 'decrease']:
    check_output(base_cmd + ['sset', volume_type, "{}%".format(vol_percentage)])
if on:
    if vol_action in ['mute'] or vol_action in ['decrease'] and vol_percentage == 0:
        check_output(base_cmd + ['sset', volume_type, "mute"])
        label = 'muted'
else:
    if vol_action in ['mute', 'increase']:
        check_output(base_cmd + ['sset', volume_type, "unmute"])

# Determining which logo to use based off of the percentage
logo = 'audio-volume-'
if vol_percentage == 0:
    logo += 'muted'
elif vol_percentage < 30:
    logo += 'low'
elif vol_percentage < 70:
    logo += 'medium'
else:
    logo += 'high'
logo += '-symbolic'

# Make the dbus method call
interface.ShowOSD({"icon": logo, "level": vol_percentage, "label": "{} Volume: {}".format(volume_type, label)})
