#!/bin/bash
pacman -S i3 compton conky nitrogen rofi maim xclip playerctl cronie
cp -R .i3 ~/.config/i3
cp .compton.conf ~/
cp .conkyrc ~/

crontab ~/.config/i3/crontabWork.txt
sudo systemctl start cronie.service
sudo systemctl enable cronie.service

git clone https://github.com/unix121/i3wm-themer
cd i3wm-themer/scripts/
sh i3wmthemer -b i3.backup
sh i3wmthemer -c
sh i3wmthemer -t Forest

