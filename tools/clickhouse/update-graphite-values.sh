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
     echo "${DIR}/../../"
}

source "$(get_source_dir)/tools/colours.sh"

if [ $# -le 3 ]; then
     echo -e "${CLR_RED}Usage: $(basename $0) <metric_path> <from> <to> <value> <limit:1000>${CLR_RESET}"
     echo -e "\nExample:\n  ${CLR_YELLOW}$(basename $0) 'collectd.graphite-frontend-ip-172-26-160-80.uptime.uptime' '2021-01-31 09:30:00' '2021-01-31 09:55:00' 10${CLR_RESET}"

     exit 1
fi

metric_path=$1
if [[ "$OSTYPE" == "darwin"* ]]; then
  lower_time_boundary=$(date -j -f "%Y-%m-%d %H:%M:%S" "$2" "+%s")
  upper_time_boundary=$(date -j -f "%Y-%m-%d %H:%M:%S" "$3" "+%s")
else
  lower_time_boundary=$(date -d "$2" +"%s")
  upper_time_boundary=$(date -d "$3" +"%s")
fi
new_value=$4
limit=${5:-10}

where_sql="WHERE (Path LIKE '${metric_path}') AND (Time >= ${lower_time_boundary}) AND (Time <= ${upper_time_boundary})"

echo -e "\nFirst check which records would be updated with:"
echo -e "  ${CLR_YELLOW}SELECT * from graphite.graphite_distributed ${where_sql} LIMIT ${limit}${CLR_RESET}"

# See https://clickhouse.com/docs/en/sql-reference/statements/alter/update/
# NOTE: Each ALTER statement runs asynchronously
echo -e "\nThen execute the update statement in each shard:"
echo -e "  ${CLR_YELLOW}ALTER TABLE graphite.graphite UPDATE Value = ${new_value} ${where_sql}${CLR_RESET}"
