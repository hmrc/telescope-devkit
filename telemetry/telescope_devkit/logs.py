import tempfile
from datetime import datetime

import boto3
from mypy_boto3_logs import CloudWatchLogsClient
from rich.errors import MarkupError

from telemetry.telescope_devkit.cli import get_console
from telemetry.telescope_devkit.logger import get_app_logger

logger = get_app_logger()
console = get_console()


def _get_latest_log_stream(logs_client: CloudWatchLogsClient, group_name: str) -> dict:
    stream_response = logs_client.describe_log_streams(
        logGroupName=group_name,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    return stream_response["logStreams"].pop()


def get_latest_cloudwatch_logs(logs_client: CloudWatchLogsClient, group_name: str, print_to_screen: bool = False) -> None:

    console.print(f"Fetching CloudWatch logs for log-group {group_name}")
    latest_log_stream = _get_latest_log_stream(logs_client, group_name)
    log_stream_name = latest_log_stream['logStreamName']
    first_event_timestamp = latest_log_stream['firstEventTimestamp']
    last_event_timestamp = latest_log_stream['lastEventTimestamp']
    first_event_datetime = datetime.fromtimestamp(int(first_event_timestamp) / 1000)
    last_event_datetime = datetime.fromtimestamp(int(last_event_timestamp)/1000)
    console.print(f"Latest log stream is '{log_stream_name}', first event time is {first_event_datetime}, " +
                  f"last event time is {last_event_datetime}")

    export_filename = tempfile.gettempdir() + "/" + f"{group_name}_{log_stream_name}.log".replace("/", "-").strip("-")
    console.print(f"Saving log events to '[yellow]{export_filename}[/yellow]'")
    file = open(export_filename, 'w')

    try:
        log_events = logs_client.get_log_events(
            logGroupName=group_name,
            logStreamName=latest_log_stream['logStreamName'],
            startTime=latest_log_stream['firstEventTimestamp'],
            endTime=latest_log_stream['lastEventTimestamp'],
            startFromHead=True,
        )
        if print_to_screen:
            logger.info(f"Displaying {len(log_events['events'])} log events")
        for event in log_events['events']:
            if print_to_screen:
                console.print(event['message'], end="")
            file.write(event['message'])

        while 'nextForwardToken' in log_events:
            log_events = logs_client.get_log_events(
                logGroupName=group_name,
                logStreamName=latest_log_stream['logStreamName'],
                endTime=latest_log_stream['lastEventTimestamp'],
                nextToken=log_events["nextForwardToken"],
                startFromHead=True
            )
            if print_to_screen:
                input("Press Enter to display the next %s log events " % len(log_events['events']))
            for event in log_events['events']:
                try:
                    if print_to_screen:
                        console.print(event['message'], end="")
                    file.write(event['message'])
                except MarkupError:
                    print(event['message'])
    except Exception as e:
        logger.error(e)
    finally:
        file.close()


class LogsCli(object):
    def __init__(self):
        self.logs_client = boto3.client('logs')

    def codebuild(self, project_name: str, print_to_screen: bool = False) -> None:
        get_latest_cloudwatch_logs(self.logs_client, f"/aws/codebuild/{project_name}", print_to_screen)
