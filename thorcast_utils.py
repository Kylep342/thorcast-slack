import os
import re

import requests


THORCAST_API_URL = os.environ['THORCAST_API_URL']


def help_message():
    return """
    Usage:

    All commands must be prefixed with one of the following:
    prefix = (!thorcast|!thor|@Thorcast)

    --------

    Get a forecast for a chosen city, state, and period
    prefix city, state{{, period }}

    Examples:
    !thor Chicago, IL, Tomorrow night
    !thorcast Los Angeles, California
    @Thorcast New York City, New York, Wednesday

    --------

    Get a random forecast:
    prefix random

    --------

    Get an hourly forecast for a chosen city and state
    prefix city, state, hourly{{, hours }}

    Examples:
    !thor Muncie, IN, hourly
    !thorcast Santa Fe, New Mexico, hourly, 8
    """.replace('^[\t]+', '').replace('[\t] +$', '\n')


def handle_error(http_resp):
    data = http_resp.json()
    if http_resp.status_code == 404:
        message = f"""{data['error']}
        Your inputs:
        City: {data['city']}
        State: {data['state']}
        Period: {data['period']}
        Please ensure you've spelled everything correctly, then try again.
        """.replace(r'^[\t ]+', '').replace(r'[\t ]+', '\n')
    elif http_resp.status_code == 500:
        message = data['message']
    return message


def get_detailed_forecast(url):
    resp = requests.get(url)
    if resp.status_code == 200:
        api_resp = resp.json()
        return f"{api_resp['period']}'s forecast for {api_resp['city']}, {api_resp['state']}:\n{api_resp['forecast']}"
    else:
        return handle_error(resp)


def get_hourly_forecast(url):
    resp = requests.get(url)
    if resp.status_code == 200:
        api_resp = resp.json()
        return f"{api_resp['hours']} hour forecast for {api_resp['city']}, {api_resp['state']}:\n{api_resp['forecast']}"


def random_forecast():
    url = f'{THORCAST_API_URL}/api/forecast/detailed/random'
    return get_detailed_forecast(url)


def forecast_control(city, state, period=None, hours=None):
    city = city.replace(' ', '+')
    state = state.replace(' ', '+')
    if period == 'hourly':
        url = f"{THORCAST_API_URL}/api/forecast/hourly?city={city}&state={state}{('&hours=' + hours) if hours else ''}"
        return get_hourly_forecast(url)
    elif period:
        period = period.replace(' ', '+')
        url = f"{THORCAST_API_URL}/api/forecast/detailed?city={city}&state={state}&period={period}"
        return get_detailed_forecast(url)
    else:
        url = f"{THORCAST_API_URL}/api/forecast/detailed?city={city}&state={state}"
        return get_detailed_forecast(url)


def process_command(cmd, cmd_prefix):
    cmd_re = f'{cmd_prefix} (?:(help|random)|(?:([a-zA-Z ]+), ?([a-zA-Z ]+),? ?([a-zA-Z ]+)?,? ?([0-9]+)?))$'
    try:
        matches = re.match(cmd_re, cmd).groups()
        if not matches[0]:
            message = forecast_control(*matches[1:])
        elif not matches[0] and matches[3].lower() == 'hourly':
            matches[3] == 'hourly'
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
