# -*- coding: utf-8 -*-

import json as _json

import requests as _requests
import click as _click

from .config import get_config

import taskmanager.models.schemas as _schema


@_click.group(short_help="command to get/create/update queues")
def queue():
    pass


@queue.command(short_help="List all queues")
@_click.option("--json", is_flag=True)
@_click.option("--csv", is_flag=True)
def list(json, csv):
    cfg = get_config()
    result = _requests.get("{server}/queues".format(**cfg)).json()
    if result["result"] != "OK":
        _click.echo("Couldn't receive data. Error: {error}".format(**result))
        return
    data = _schema.WorkerQueue(many=True).load(result).data
    if json:
        _click.echo(_json.dumps(data))
    elif csv:
        _click.echo(",".join(data[0].keys()))
        for queue in data:
            _click.echo(
                ",".join(
                    str(v) for v in queue.values()
                )
            )
    else:
        for queue in data:
            _click.echo(queue["name"])
