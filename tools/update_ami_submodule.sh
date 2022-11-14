#!/usr/bin/env bash

# This script will iterate through the Telemetry AMI repositories and refresh its telemetry-ami-resources submodule.
# Usage: ./tools/update_ami_submodule.sh </path/to/source/root> <Jira Ticket> <Co-Authored by>
#   e.g: ./tools/update_ami_submodule.sh /Users/leemyring/source/hmrc "TEL-3074" "Co-authored-by: Stephen Palfreyman <18111914+sjpalf@users.noreply.github.com>"

echo "INFO: Validating commands"
[ -z "$(command -v git)" ] && { echo "ERROR: missing git"; exit 1; }
[ -z "$(command -v gh)" ] && { echo "ERROR: missing gh"; exit 1; }

SRC_ROOT_DIR="${1}"
JIRA_TICKET="${2}"
CO_AUTHOR="${3}"

cd "${SRC_ROOT_DIR}" || exit

echo "" > "${SRC_ROOT_DIR}/pr_output.txt"

for f in aws-ami-elastic-base \
         aws-ami-elastic-data \
         aws-ami-elastic-ingest \
         aws-ami-elastic-ingest-performance-agent \
         aws-ami-elastic-loadtest \
         aws-ami-elastic-master \
         aws-ami-elastic-query \
         aws-ami-grafana \
         aws-ami-graphite-base \
         aws-ami-graphite-relay \
         aws-ami-kibana \
         aws-ami-telemetry-1804-ubuntu-base \
         aws-ami-telemetry-clickhouse \
         aws-ami-telemetry-ecs-node \
         aws-ami-telemetry-ingest-backstop \
         aws-ami-telemetry-proxy \
         aws-ami-telemetry-sensu \
         aws-ami-telemetry-zookeeper \
         aws-ami-uchiwa;
do
  (
    export DIRENV_LOG_FORMAT=  && \
    [[ -d ${f} && -d ${f}/.git && -f ${f}/.gitmodules ]] && \
    cd "$f" && \
    echo "Checking repository '${f}'" && \
    git checkout main && \
    git pull --rebase && \
    git fetch --prune && \
    git checkout -b "${JIRA_TICKET}" && \
    git submodule update --init --remote --recursive && \
    git add resources && \
    git commit --no-verify --message="${JIRA_TICKET}: update submodules" --message="${CO_AUTHOR}" && \
    git push --set-upstream origin "${JIRA_TICKET}" && \
    gh pr create --fill >> "${SRC_ROOT_DIR}/pr_output.txt" && \
    echo ""
  )
done;
