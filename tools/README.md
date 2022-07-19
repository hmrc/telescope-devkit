# Extra tools

## `all-the-buckets.sh` 

Lists all the S3 buckets provisioned in the Telemetry accounts. Output is in CSV format, ready to be exported to a file and imported into a Google Spreadsheet.

## `cleanup-cw-log-subscriptions.sh`

Deletes the `log-handler-lambda-subscription` for a defined set of CloudWatch Log Groups.

## `clickhouse/update-graphite-values.sh`

Updates datapoints directly in ClickHouse. Use it wisely.

For details see the [Updating data in ClickHouse](https://confluence.tools.tax.service.gov.uk/display/TEL/Updating+data+in+ClickHouse) guide in Confluence.

## `password-generator.sh`

It generates random passwords. Default password length is 32 characters.

## `yaml-expand.sh`

Resolves and expands anchors and aliases in YAML files which some may find useful for debugging. 