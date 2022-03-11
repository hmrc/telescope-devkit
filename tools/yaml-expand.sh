#!/usr/bin/env bash

get_source_dir() {
     SOURCE="${BASH_SOURCE[0]}"
     # While $SOURCE is a symlink, resolve it
     while [ -h "$SOURCE" ]; do
          DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
          SOURCE="$( readlink "$SOURCE" )"
          # If $SOURCE was a relative symlink (so no "/" as prefix, need to resolve it relative to the symlink base directory
          [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
     done
     DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
     echo "${DIR}/../"
}

source "$(get_source_dir)/tools/colours.sh"

COMMAND=spruce

check_spruce() {
  if ! command -v ${COMMAND} &> /dev/null
  then
      echo -e "${CLR_RED}ERROR: command \`${COMMAND}\` could not be found.${CLR_RESET}"
      cat << EOT

  To install it please follow the instructions in
  https://github.com/geofffranks/spruce#how-do-i-get-started
  and re-run this script.
EOT

      return 1
  fi
}

check_spruce || exit 1

if [ $# -lt 1 ]; then
     echo -e "${CLR_RED}Usage: $(basename $0) <source_yaml_filepath> [<expanded_yaml_filepath>] ${CLR_RESET}"

     exit 1
fi

source_yaml_filepath=${1}

filename=$(basename -- "${source_yaml_filepath}")
extension="${filename##*.}"
filename="${filename%.*}"

if [ $# -lt 2 ]; then
  expanded_yaml_filepath=$(dirname "${source_yaml_filepath}")/.${filename}.expanded.${extension}
else
  expanded_yaml_filepath=${2}
fi


${COMMAND} merge "${source_yaml_filepath}" > "${expanded_yaml_filepath}"

echo -e "Source YAML has been expanded and is now available at: ${CLR_YELLOW}${expanded_yaml_filepath}${CLR_RESET}"
