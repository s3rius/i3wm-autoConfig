#!/bin/bash

LOG_FILE="$HOME/i3-readme.txt"

print(){
	echo "[i3wm-installer] $1"
}

printlog(){
  echo "[i3-wm-installer] $1"
  echo "$1" >> $LOG_FILE
}

i3path="$HOME/.config/i3"

if [ -x "$(command -v pikaur)" ]; then
  print "Found pikaur installation"
else
  print "Pikaur was not found."
  git clone https://aur.archlinux.org/pikaur.git
  cd pikaur
  makepkg -fsri
  cd ..
  rm -rfv pikaur/
fi

sudo pacman -S --needed $(cat deps.pacman)
sudo pikaur -S --noedit --nodiff --needed $(cat deps.pikaur) 

pip install --user tuijam
pip install -r i3/requirements.txt --user

mv $i3path $HOME/.config/i3.old
print "$i3path moved into ~/.config/i3.old"
cp -R i3 $HOME/.config/
print "copied new configs into $i3path"
cp .compton.conf ~/
print "Copied compton config into ~/.compton.conf"
cp .conkyrc ~/
print "Copied conkyrc config into ~/.conkyrc"

if [ "$(crontab -l | head -n1 | cut -d " " -f1)" == "*" ]
then 
	print "Cron have shelduded jobs"
	crontab -l > lastjobs.txt
	cat i3/crontabWork.txt >> lastjobs.txt
	print "appending in lastjobs.txt"
	crontab lastjobs.txt
	print "added new jobs in cron"
else
	print "Cron does not have any jobs"
	crontab i3/crontabWork.txt
	print "Added new job in cron for battery check"
fi
mkdir -p "$HOME/.config/rofi/themes/"

if [ -e "$HOME/.config/rofi/config" ]; then
  print "ROFI config found"
else
  touch "$HOME/.config/rofi/config"
  print "Created ROFI config"
fi

cp ./rofi_themes/hyper.rasi ~/.config/rofi/themes/hyper.rasi
print "copied rofi configuration[hyper]"
sudo systemctl start cronie.service
print "started cronie service"
sudo systemctl enable cronie.service
print "enabled cronie for autostart with system"

print " **** "
print "Installation succeed."
print "Start your i3 by running 'startx'"
print "Additional steps to configure wm."
print "Instruction will be saved in ~/i3-readme.txt"
print " **** "
print ""
rm -vf $LOG_FILE
touch $LOG_FILE
printlog "To set wallpaper run 'nitrogen'"
printlog "To change rofi theme to 'hyper' run 'rofi-theme-selector' and select 'hyper by s3rius'"
printlog "To add wallpaper to lockscreen run 'betterlockscreen -u /path/to/wallpapers'"
