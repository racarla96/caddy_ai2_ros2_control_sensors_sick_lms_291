#!/bin/bash
echo  'KERNEL=="ttyUSB*", ATTRS{idVendor}=="067b", ATTRS{idProduct}=="2303", MODE:="0666", GROUP:="dialout",  SYMLINK+="sick"' > /etc/udev/rules.d/ros2-sensor-usb-sick.rules

service udev reload
sleep 2
service udev restart

