#!/bin/bash
# constants project: https://gist.github.com/717f75e6b87606940017adf385274044.git
# creator:           Kamontat Chantrachirathumrong

# Reset
CLR_RESET='\033[0m'                # Text Reset

# Special Colors
CLR_C='\033[0;2m'                  # Default color setting
CLR_CB='\033[0;1m'                 # Default color setting and bright a little bit

# Regular Colors
CLR_BLACK='\033[0;30m'             # Black
CLR_RED='\033[0;31m'               # Red
CLR_GREEN='\033[0;32m'             # Green
CLR_YELLOW='\033[0;33m'            # Yellow
CLR_BLUE='\033[0;34m'              # Blue
CLR_PINK='\033[0;35m'              # Pink
CLR_CYAN='\033[0;36m'              # Cyan
CLR_WHITE='\033[0;37m'             # White

# Bold
CLR_B_BLACK='\033[1;30m'            # Black
CLR_B_RED='\033[1;31m'              # Red
CLR_B_GREEN='\033[1;32m'            # Green
CLR_B_YELLOW='\033[1;33m'           # Yellow
CLR_B_BLUE='\033[1;34m'             # Blue
CLR_B_PINK='\033[1;35m'             # Pink
CLR_B_CYAN='\033[1;36m'             # Cyan
CLR_B_WHITE='\033[1;37m'            # White

# Underline
CLR_U_BLACK='\033[4;30m'            # Black
CLR_U_RED='\033[4;31m'              # Red
CLR_U_GREEN='\033[4;32m'            # Green
CLR_U_YELLOW='\033[4;33m'           # Yellow
CLR_U_BLUE='\033[4;34m'             # Blue
CLR_U_PINK='\033[4;35m'             # Pink
CLR_U_CYAN='\033[4;36m'             # Cyan
CLR_U_WHITE='\033[4;37m'            # White

# Background
CLR_BG_BLACK='\033[40m'            # Black
CLR_BG_RED='\033[41m'              # Red
CLR_BG_GREEN='\033[42m'            # Green
CLR_BG_YELLOW='\033[43m'           # Yellow
CLR_BG_BLUE='\033[44m'             # Blue
CLR_BG_PINK='\033[45m'             # Pink
CLR_BG_CYAN='\033[46m'             # Cyan
CLR_BG_WHITE='\033[47m'            # White

# High Intensity
CLR_HI_BLACK='\033[0;90m'            # Black
CLR_HI_RED='\033[0;91m'              # Red
CLR_HI_GREEN='\033[0;92m'            # Green
CLR_HI_YELLOW='\033[0;93m'           # Yellow
CLR_HI_BLUE='\033[0;94m'             # Blue
CLR_HI_PINK='\033[0;95m'             # Pink
CLR_HI_CYAN='\033[0;96m'             # Cyan
CLR_HI_WHITE='\033[0;97m'            # White

# Bold High Intensity
CLR_B_HI_BLACK='\033[1;90m'           # Black
CLR_B_HI_RED='\033[1;91m'             # Red
CLR_B_HI_GREEN='\033[1;92m'           # Green
CLR_B_HI_YELLOW='\033[1;93m'          # Yellow
CLR_B_HI_BLUE='\033[1;94m'            # Blue
CLR_B_HI_PINK='\033[1;95m'            # Pink
CLR_B_HI_CYAN='\033[1;96m'            # Cyan
CLR_B_HI_WHITE='\033[1;97m'           # White

# High Intensity backgrounds
CLR_BG_HI_BLACK='\033[0;100m'        # Black
CLR_BG_HI_RED='\033[0;101m'          # Red
CLR_BG_HI_GREEN='\033[0;102m'        # Green
CLR_BG_HI_YELLOW='\033[0;103m'       # Yellow
CLR_BG_HI_BLUE='\033[0;104m'         # Blue
CLR_BG_HI_PINK='\033[0;105m'         # Pink
CLR_BG_HI_CYAN='\033[0;106m'         # Cyan
CLR_BG_HI_WHITE='\033[0;107m'        # White

# Blink
CLR_BLINK_BLACK='\033[5;30m'       # Black
CLR_BLINK_RED='\033[5;31m'         # Red
CLR_BLINK_GREEN='\033[5;32m'       # Green
CLR_BLINK_YELLOW='\033[5;33m'      # Yellow
CLR_BLINK_BLUE='\033[5;34m'        # Blue
CLR_BLINK_PINK='\033[5;35m'        # Pink
CLR_BLINK_CYAN='\033[5;36m'        # Cyan
CLR_BLINK_WHITE='\033[5;37m'       # White
