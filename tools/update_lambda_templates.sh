#!/usr/bin/env bash

# This script will iterate through the Telemetry Lambda repositories and update its telemetry-lambda-resources templates.
# Usage: ./tools/update_lambda_templates.sh </path/to/source/root> <Jira Ticket> <Co-Authored by>
#   e.g: ./tools/update_lambda_templates.sh /Users/leemyring/source/hmrc "TEL-3074" "Co-authored-by: Stephen Palfreyman <18111914+sjpalf@users.noreply.github.com>"

echo "INFO: Validating commands"
[ -z "$(command -v ag)" ] && { echo "ERROR: missing ag"; exit 1; }
[ -z "$(command -v cruft)" ] && { echo "ERROR: missing cruft"; exit 1; }
[ -z "$(command -v git)" ] && { echo "ERROR: missing git"; exit 1; }
[ -z "$(command -v gh)" ] && { echo "ERROR: missing gh"; exit 1; }

SRC_ROOT_DIR="${1}"
JIRA_TICKET="${2}"
CO_AUTHOR="${3}"

# Navigate to the root folder
cd "${SRC_ROOT_DIR}" || exit

# Clear out temp files
echo "" > "${SRC_ROOT_DIR}/pr_output.txt"
echo "" > "${SRC_ROOT_DIR}/lambda_input.txt"

# Create unique-ish Jira ticket suffix
JIRA_SUFFIX=$(date '+%Y-%m-%d')

# Use Silver Searcher to grep through all Cruft controlled Lambda templated repos and export list to file
ag --files-with-matches \
   --file-search-regex .cruft.json \
   --hidden \
   "\"template\": \"https:\/\/github\.com\/hmrc\/telemetry\-lambda\-resources\",$" | awk -F/ '{print $1}' > "${SRC_ROOT_DIR}/lambda_input.txt"

# Iterate through the file generated in step above and run a Cruft update and create PRs as appropriate
# https://github.com/koalaman/shellcheck/wiki/SC2013
while IFS= read -r f
do
  (
      export DIRENV_LOG_FORMAT=  && \
      [[ -d ${f} && -d ${f}/.git && -f ${f}/.cruft.json ]] && \
      cd "$f" && \
      echo "Checking repository '${f}'"
      git checkout main && \
      git pull --rebase && \
      git fetch --prune && \
      git checkout -b "${JIRA_TICKET}-${JIRA_SUFFIX}" && \
      cruft update --skip-apply-ask && \
      cruft diff | git apply --allow-empty && \
      git add . && \
      pre-commit run --all-files && \
      git commit --no-verify --message="${JIRA_TICKET}: update lambda templates" --message="${CO_AUTHOR}" && \
      git push --set-upstream origin "${JIRA_TICKET}-${JIRA_SUFFIX}" && \
      gh pr create --fill >> "${SRC_ROOT_DIR}/pr_output.txt" && \
      echo ""
    )
done < "${SRC_ROOT_DIR}/lambda_input.txt"
