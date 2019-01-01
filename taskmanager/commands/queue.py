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
@_click.option("--size", required=False, default=100, help="Limit Items in result")
@_click.option("--page", required=False, default=0, help="Page for the result")
def list(format, size, page):
    cfg = get_config()
    params = f"include_data=1&page[size]={size}&page[number]={page}"
    result = _requests.get(
        "{server}/workerqueues?{params}".format(
            params=params,
            **cfg
        )
    ).json()
    if result["result"] != "OK":
        _click.echo("Couldn't receive data. Error: {error}".format(**result))
        return
    result.pop("meta")
    data = _schema.WorkerQueue(many=True).load(result)
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
    data = _schema.WorkerQueue().load(result).data
    _click.secho(f"Queue created {data}", fg="green")
