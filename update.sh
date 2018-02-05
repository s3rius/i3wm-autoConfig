#!/bin/bash


print(){
 echo "[i3 updater] $1"
}

path=$(pwd)
dir="$(dirname $(readlink -f $0))"

cd  $dir
print "Working in $dir" 
print "started updating i3wm configs"
rm -rf i3
print "deleted last i3 config"
cp -R ~/.config/i3 .
if [ -d "$(pwd)/i3" ]
then
	print "loaded new i3 config"
else
	print "ERROR: can't load i3 config check ~/.config/i3 for existance"
	exit -1
fi
print "loaded new config"
cp ~/.conkyrc .
print "Loaded .conkyrc"
cp ~/.compton.conf .
print "Loaded compton.conf"
cd $path
print "returned into $path" 

