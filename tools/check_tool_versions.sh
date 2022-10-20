#!/usr/bin/env bash
# This script is to make sure both .tool-versions (ASDF) and .<tool>-version (individual version managers) are pointing
#  to the same version of the given tool, to avoid divergence.

# Variables
root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
asdf_version_file="$root_dir/.tool-versions"
declare -a tools=("python" "terraform" "terragrunt")
all_synced=true

# Checks
for tool in "${tools[@]}"
do
  tool_version_file="$root_dir/.$tool-version"
  if diff <(cat "$asdf_version_file" | grep "$tool " | awk '{print $2}') <(cat "$tool_version_file") > /dev/null ; then
    echo "$tool version files are in sync"
  else
    echo -e "$tool version divergence detected!\t Cross-check $(basename ${asdf_version_file}) and $(basename ${tool_version_file})"
    all_synced=false
  fi
done

# Verdict
if $all_synced; then
  exit 0
else
  exit 1
fi
