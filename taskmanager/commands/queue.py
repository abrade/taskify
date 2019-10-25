# -*- coding: utf-8 -*-

import json as _json

import requests as _requests
import click as _click

import taskmanager.models.schemas as _schema
import taskmanager.commands.base as _base

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
    params = f"include_data=1&page[size]={size}&page[number]={page}"
    response = _base.get_response(
        "{{server}}/workerqueues?{params}".format(
            params=params,
        )
    )

    if not response:
        return
    result = response.json()
    result.pop("meta")
    if 'data' in result:
        result = result.pop("data")
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

    params = _schema.WorkerQueue().dump(queue)
    result = _base.post_response(
        "{{server}}/workerqueues",
        data=_json.dumps(params)
    )

    if not result:
        return
    result = result.json()
    if 'data' in result:
        result = result.pop("data")

    data = _schema.WorkerQueue().load(result)
    _click.secho(f"Queue created {data}", fg="green")
