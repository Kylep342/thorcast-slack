import os
import time

import slackclient
from slackclient import SlackClient

import thorcast_utils as utils

BOT_TOKEN = os.environ['SLACK_API_TOKEN']


def thorcast_slack():
    sc = SlackClient(BOT_TOKEN)
    sc.rtm_connect(with_team_state=False)
    thorcast_id = sc.api_call('auth.test')['user_id']
    while True:
        try:
            utils.process_events(sc, sc.rtm_read(), thorcast_id)
            time.sleep(1)
        except slackclient.server.SlackConnectionError:
            sc.rtm_connect(with_team_state=False)


if __name__ == "__main__":
    thorcast_slack()
