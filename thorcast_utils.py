import os
import re

import requests


THORCAST_API_URL = os.environ['THORCAST_API_URL']


def help_message():
    return """
    Usage:

    --------

    Get a forecast for a chosen city, state, and period
    (!thorcast|!thor|@Thorcast) city, state{{, period }}

    Examples:
    !thor Chicago, IL, Tomorrow night
    !thorcast Los Angeles, California
    @Thorcast New York City, New York, Wednesday

    --------

    Get a random forecast:
    (!thorcast|!thor|@Thorcast) random
    """.replace('^[\t]+', '').replace('[\t] +$', '\n')


def handle_error(http_resp):
    data = http_resp.json()
    if http_resp.status_code == 404:
        message = f"""{data['info']}
        Your inputs:
        City: {data['city']}
        State: {data['state']}
        Period: {data['period']}
        Please ensure you've spelled everything correctly, then try again.
        """.replace(r'^[\t ]+', '').replace(r'[\t ]+', '\n')
    elif http_resp.status_code == 500:
        message = data['message']
    return message


def get_forecast(url):
    resp = requests.get(url)
    if resp.status_code == 200:
        api_resp = resp.json()
        return f"{api_resp['period']}'s forecast for {api_resp['city']}, {api_resp['state']}:\n{api_resp['forecast']}"
    else:
        return handle_error(resp)


def random_forecast():
    url = f'{THORCAST_API_URL}/api/forecast/random'
    return get_forecast(url)


def forecast_control(city, state, period=None):
    city = city.replace(' ', '+')
    state = state.replace(' ', '+')
    if period:
        period = period.replace(' ', '+')
        url = f"{THORCAST_API_URL}/api/forecast/city={city}&state={state}&period={period}"
    else:
        url = f"{THORCAST_API_URL}/api/forecast/city={city}&state={state}"
    return get_forecast(url)


def process_command(cmd, cmd_prefix):
    cmd_re = f'{cmd_prefix} (?:(help|random)|(?:([a-zA-Z ]+), ?([a-zA-Z ]+),? ?([a-zA-Z ]+)?))$'
    try:
        matches = re.match(cmd_re, cmd).groups()
        if not matches[0]:
            message = forecast_control(*matches[1:])
        else:
            if matches[0] == 'help':
                message = help_message()
            else:
                message = random_forecast()
    except AttributeError:
        return
    else:
        return message


def process_events(slack_client, slack_events, thorcast_id):
    for event in slack_events:
        if event['type'] == 'message' and not 'subtype' in event:
            uid, msg, channel = event['user'], event['text'], event['channel']
            if uid == thorcast_id:
                return
            cmd_prefix = f"^(?:(?:!thor(?:cast)?)|(?:{thorcast_id}))"
            if re.match(cmd_prefix, msg):
                message = process_command(msg, cmd_prefix)
                if message:
                    slack_client.api_call(
                        'chat.postMessage',
                        channel=channel,
                        text=message
                    )