#!/bin/bash
pacman -S i3 compton conky nitrogen rofi maim xclip playerctl
cp -R .i3 ~/.config/i4
cp .compton.conf ~/
cp .conkyrc ~/

git clone https://github.com/unix121/i3wm-themer
cd i3wm-themer/scripts/
sh i3wmthemer -b i3.backup
sh i3wmthemer -c
sh i3wmthemer -t Forest

