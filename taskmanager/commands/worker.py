# -*- coding: utf-8 -*-

import json as _json

import requests as _requests
import click as _click

from .config import get_config

import taskmanager.models.schemas as _schema


@_click.group(short_help="command to get/create/update workers")
def worker():
    pass


@worker.command(short_help="List all workers")
@_click.option(
    "--format",
    type=_click.Choice(["name", "json", "csv"]),
    default="name",
    help="Select output format (default: name)"
)
def list(format):
    cfg = get_config()
    result = _requests.get("{server}/workers".format(**cfg)).json()
    if result["result"] != "OK":
        _click.echo("Couldn't receive data. Error: {error}".format(**result))
        return
    data = _schema.Worker().load(result, many=True).data
    if format == "json":
        _click.echo(_json.dumps(data))
    elif format == "csv":
        _click.echo(",".join(data[0].keys()))
        for worker in data:
            _click.echo(
                ",".join(
                    str(v) for v in worker.values()
                )
            )
    else:
        for worker in data:
            _click.echo(worker["name"])


@worker.command(short_help="Create new worker")
@_click.argument("name")
def add(name):
    cfg = get_config()
    params = {
        'name': name
    }
    params = _schema.Worker().dump(params).data
    result = _requests.post(
        "{server}/workers".format(**cfg),
        data=_json.dumps(params)
    ).json()
    if result["result"] != "OK":
        _click.echo(
            "Error while creating new worker: {error}".format(**result))
    else:
        _click.echo("Worker created.")


@worker.command(short_help="Update worker")
@_click.argument("worker_id", type=int)
@_click.argument("worker")
def update(worker_id, worker):
    cfg = get_config()
    result = _requests.patch(
        "{server}/workers/{worker_id}".format(
            worker_id=worker_id,
            **cfg,
        ),
        data=_json.dumps({"name": worker})
    ).json()
    if result["result"] != "OK":
        _click.echo("Error while updating worker: {error}".format(**result))
    else:
        _click.echo("Worker updated.")
