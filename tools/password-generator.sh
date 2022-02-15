#!/usr/bin/env bash
set -eo pipefail

default_password_length=32

if [[ "$#" -gt 0 ]]; then
  password_length=$1
else
  password_length=$default_password_length
fi

if [[ "$OSTYPE" == "darwin"* ]]; then
  LC_ALL=C < /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c${password_length}
else
  cat /dev/urandom | tr -dc '_A-Z-a-z-0-9' | fold -w $password_length | head -n 1
fi
