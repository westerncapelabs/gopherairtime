"""Send SMSes via a Vumi Go HTTP API."""

import json
import logging

import requests

from django.conf import settings


class SmsSetupError(Exception):
    """Raised when creating an SMS sender fails."""


class SmsSendingError(Exception):
    """Raised when SMS sending fails."""


class SmsSender(object):
    def __init__(self):
        """Override in sub-classes."""
        pass

    def send_sms(self, to_addr, content):
        """Send an SMS.

        Raises SmsSendingError if an error occurs.

        Override in sub-classes.
        """
        raise NotImplementedError


class VumiGoSender(SmsSender):
    def __init__(self, api_url, account_id, conversation_id,
                 conversation_token):
        self.api_url = api_url
        self.account_id = account_id
        self.conversation_id = conversation_id
        self.conversation_token = conversation_token

    def _api_url(self):
        return "%s/%s/messages.json" % (self.api_url, self.conversation_id)

    def send_sms(self, to_addr, content):
        headers = {'content-type': 'application/json; charset=utf-8'}
        payload = {
            "content": content,
            "to_addr": to_addr,
        }
        response = requests.put(self._api_url(), auth=(self.account_id, self.conversation_token), headers=headers,
                                data=json.dumps(payload))

        if response.status_code != requests.codes.ok:
            raise SmsSendingError("Failed to send SMS, response code: %d,"
                                  " data: %r" % (response.status_code,
                                                 response.content))
        try:
            reply = response.json()
        except ValueError:
            raise SmsSendingError("Bad response received from Vumi Go"
                                  " HTTP API. Excepted JSON, received:"
                                  " %r" % (response.content,))
        return reply


class LoggingSender(SmsSender):
    def __init__(self, logger="magriculture.sms", level=logging.INFO):
        self._logger = logging.getLogger(logger)
        self._level = level

    def send_sms(self, to_addr, content):
        self._logger.log(self._level, "SMS to %r: %r" % (to_addr, content))


def create_sender(sms_config):
    """Factory for creating an SMS sender from settings.

       Update this is you want to add new sender types.
       """
    if sms_config is None:
        raise SmsSetupError("SMS sending not configured."
                            " Set SMS_SETTINGS in settings.py")
    sender_type = sms_config.pop('sender_type', None)
    if sender_type is None:
        raise SmsSetupError("SMS_SETTINGS contains no sender_type")
    senders = {
        "vumigo": VumiGoSender,
        "logging": LoggingSender,
    }
    sender_cls = senders.get(sender_type)
    if sender_cls is None:
        raise SmsSetupError("Unknown sender_type %r. Available types"
                            " are: %s" % (sender_type, senders.keys()))
    return sender_cls(**sms_config)


default_sender = create_sender(getattr(settings, 'SMS_CONFIG', None))
send_sms = default_sender.send_sms
