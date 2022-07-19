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

telemetry_aws_accounts=(
    telemetry-internal-base
    telemetry-internal-integration
    telemetry-internal-lab01
    telemetry-internal-lab02
    telemetry-internal-lab03
    telemetry-internal-lab04
    telemetry-internal-staging
    telemetry-internal-telemetry
    telemetry-mdtp-development
    telemetry-mdtp-externaltest
    telemetry-mdtp-integration
    telemetry-mdtp-management
    telemetry-mdtp-production
    telemetry-mdtp-qa
    telemetry-mdtp-staging
)

output_file=$(get_source_dir)/tools/all-the-buckets.csv

[[ ! -f "${output_file}" ]] && touch "${output_file}"

echo "AWS Account,Bucket Name" > "${output_file}"

for account in "${telemetry_aws_accounts[@]}"; do
    echo -en "Collecting S3 buckets for account ${CLR_GREEN}${account}${CLR_RESET} ... "
    while IFS= read -r bucket; do
        echo "${account},${bucket}" >> "${output_file}"
    done <<< "$(aws-profile -p "${account}"-RoleTelemetryEngineer aws s3 ls | awk '{ print $3 }')"
    echo -e "done."
done
