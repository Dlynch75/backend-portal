"""
Utility functions for local messages

"""

import json
import os

from school_project.settings import MSG_LOCALE


def get_message(msg_code=None):
    """Get localized message according to the given code.
    Locale used is configured in settings
    Args:
        msg_code ([int], mandatory): [Message code described in module locale]
    """
    # msg_code not provided
    if not msg_code:
        raise ValueError("msg_code not provided")

    try:
        # Open locale messages
        with open(
                os.path.dirname(os.path.realpath(__file__)) + "/message.json", "r", encoding='utf-8') as locale_file:
            message_dict = json.load(locale_file)

            return message_dict[str(msg_code)]["msg"][MSG_LOCALE]

    except Exception as e:
        print(e)
        return "Message not found against code " + str(msg_code)
