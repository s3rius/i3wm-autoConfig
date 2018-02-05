#!/bin/bash

print(){
	echo "[i3wm-installer] $1"
}

i3path="~/.config/i3"

sudo pacman -S i3 compton conky nitrogen rofi maim xclip playerctl cronie help2man
mv $i3path ~/.config/i3.old
print "$i3path moved into ~/.config/i3.old"
cp -R i3 ~/.config/
print "copied new configs into $i3path"
cp .compton.conf ~/
print "Copied compton config into ~/.compton.conf"
cp .conkyrc ~/
print "Copied conkyrc config into ~/.conkyrc"

print "[git] started clone of /haikarainen/light repo"
print "[git] that library needs for adjust brightness on pc"
git clone --progress https://github.com/haikarainen/light.git 2> gitLightOutput.log
print "[git] output is shown in file gitLightOutput.log"
cd light
print "[making] $(sudo make)"
print "[installing light]$(sudo make install)"
cd ..
rm -rf light/
print "removed light repo"

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


sudo systemctl start cronie.service
print "started cronie service"
sudo systemctl enable cronie.service
print "enabled cronie for autostart with system"

#pwd
#sudo git clone https://github.com/unix121/i3wm-themer.git
#cd i3wm-themer/scripts/
#sh i3wmthemer -b i3.backup
#sh i3wmthemer -c
#sh i3wmthemer -t Forest

