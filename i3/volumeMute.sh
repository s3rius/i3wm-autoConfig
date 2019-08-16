#!/bin/bash

amixer -c 0 get Master | grep Mono: | cut -d " " -f8 | grep -oP '[a-z]*'
