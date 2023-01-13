#!/usr/bin/env bash


source ../../../../zulip-api-py3-venv/bin/activate
zulip-botserver --config-file ./zuliprc --bot-name=calendarbot
