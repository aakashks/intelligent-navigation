#!/bin/bash

sudo service xrdp stop
sudo service dbus stop

pkill -u user1
pkill xfce4-session
pkill xfce4

ps aux | grep -E 'xrdp|xfce4|dbus' | grep -v grep

echo "Cleanup completed. You can now safely commit the container."
