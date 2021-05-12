# telescope-devkit

[![Brought to you by Telemetry Team](https://img.shields.io/badge/MDTP-Telemetry-40D9C0?style=flat&labelColor=000000&logo=gov.uk)](https://confluence.tools.tax.service.gov.uk/display/TEL/Telemetry)

A Python-based tool to facilitate the interaction with Telemetry resources deployed to AWS.

## Requirements

* [Docker](https://www.docker.com/)

### Extra requirements for development (optional)

* [Python 3.8+](https://www.python.org/downloads/release)
* [Poetry](https://python-poetry.org/)

## Quickstart

Interactions with this tool can be done through the `telescope` bash script.

* Step 1: build a Docker image with the Python application;
* Step 2: install a symlink to `bin/telescope` in `/usr/local/bin/telescope`;

The command below will do both:

```shell
❯ make install
```

Assuming that `/usr/local/bin` is in your `PATH` then just launch the binary as:

```shell
❯ telescope
 
NAME
    telescope

SYNOPSIS
    telescope COMMAND

COMMANDS
    COMMAND is one of the following:

     ec2

     logs

     update
```

## Examples

### EC2 instances

Get list of EC2 of `clickhouse` instances in `internal-telemetry`:

```shell
❯ aws-profile -p telemetry-internal-telemetry-RoleTelemetryEngineer bin/telescope ec2 instances clickhouse
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Instance Name             ┃ Instance Id         ┃ Instance Type ┃ Availability Zone ┃ Launch Time         ┃ Private IP Address ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ clickhouse-server-shard_1 │ i-0ca3e79ad092d4074 │ c5.2xlarge    │ eu-west-2a        │ 2021-02-11 10:18:14 │ 10.7.0.130         │
│ clickhouse-server-shard_2 │ i-0b696af20091baaa3 │ c5.2xlarge    │ eu-west-2a        │ 2021-02-11 10:17:56 │ 10.7.0.167         │
│ clickhouse-server-shard_2 │ i-0595b1db0e4579e6d │ c5.2xlarge    │ eu-west-2b        │ 2021-02-11 10:35:50 │ 10.7.1.36          │
│ clickhouse-server-shard_1 │ i-01354aa415b746c29 │ c5.2xlarge    │ eu-west-2b        │ 2021-02-11 10:34:23 │ 10.7.1.216         │
│ clickhouse-server-shard_2 │ i-05012c0699bb0fe9e │ c5.2xlarge    │ eu-west-2c        │ 2021-02-11 10:12:11 │ 10.7.2.68          │
│ clickhouse-server-shard_1 │ i-0cf036cab2476e233 │ c5.2xlarge    │ eu-west-2c        │ 2021-02-11 10:04:26 │ 10.7.2.12          │
└───────────────────────────┴─────────────────────┴───────────────┴───────────────────┴─────────────────────┴────────────────────┘
```

### Update telescope

To update `telescope`:

```shell
❯ telescope update
```

### License

This code is open source software licensed under the [Apache 2.0 License]("http://www.apache.org/licenses/LICENSE-2.0.html").
