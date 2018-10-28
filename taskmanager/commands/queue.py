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
@_click.option(
    "--format",
    type=_click.Choice(["name", "json", "csv"]),
    default="name",
    help="Select output format (default: name)"
)
def list(format):
    cfg = get_config()
    result = _requests.get("{server}/workerqueues".format(**cfg)).json()
    if result["result"] != "OK":
        _click.echo("Couldn't receive data. Error: {error}".format(**result))
        return
    data = _schema.WorkerQueue(many=True).load(result).data
    if format == "json":
        _click.echo(_json.dumps(data))
    elif format == "csv":
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


@queue.command(short_help="Add a queue")
@_click.argument("name")
def add(name):
    cfg = get_config()
    queue = {
        'name': name,
        'state': 'active',
    }

    params = _schema.WorkerQueue().dump(queue).data
    result = _requests.post(
        "{server}/workerqueues".format(**cfg),
        data=_json.dumps(params)
    ).json()

    if result["result"] != "OK":
        _click.secho(
            "Couldn't get result. Error: {error}".format(
                **result
            ),
            fg="red",
        )
        return
    _click.secho("Queue created", fg="green")
