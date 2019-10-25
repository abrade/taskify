# -*- coding: utf-8 -*-

import json as _json

import requests as _requests
import click as _click

import taskmanager.models.schemas as _schema
import taskmanager.commands.base as _base


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
@_click.option("--size", required=False, default=100, help="Limit Items in result")
@_click.option("--page", required=False, default=0, help="Page for the result")
def list(format, size, page):
    params = f"include_data=1&page[size]={size}&page[number]={page}"
    result = _base.get_response(
        "{{server}}/workers?{params}".format(
            params=params,
        )
    )
    if not result:
        return
    result = result.json()
    result.pop("meta")
    data = _schema.Worker().load(result, many=True)
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
    params = {
        'name': name
    }
    params = _schema.Worker().dump(params).data
    result = _base.post_response(
        "{server}/workers",
        data=_json.dumps(params)
    )
    if not result:
        return

    _click.echo("Worker created.")


@worker.command(short_help="Update worker")
@_click.argument("worker_id", type=int)
@_click.argument("worker")
def update(worker_id, worker):
    params = _schema.Worker().dump({"name": worker}).data
    result = _base.patch_response(
        "{{server}}/workers/{worker_id}".format(
            worker_id=worker_id,
        ),
        data=_json.dumps(params)
    )
    if not result:
        return
    _click.echo("Worker updated.")
