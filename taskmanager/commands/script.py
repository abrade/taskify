# -*- coding:utf-8 -*-

import json as _json

import requests as _requests
import click as _click

from .config import get_config

import taskmanager.models.schemas as _schema


@_click.group(short_help="command to get/create/update scripts")
def script():
    pass


@script.command(short_help="Get all scripts")
@_click.option("--json", is_flag=True)
@_click.option("--csv", is_flag=True)
def list(json, csv):
    cfg = get_config()
    result = _requests.get(
        "{server}/scripts?include_data=1".format(**cfg),
    ).json()

    if result["result"] != "OK":
        _click.echo("Couldn't receive data. Error: {error}".format(**result))
        return

    data = _schema.Script(many=True).load(result).data
    if json:
        _click.echo(_json.dumps(data))
    elif csv:
        _click.echo(",".join(data[0].keys()))
        for script in data:
            output = []
            for _key, value in script.items():
                if not isinstance(value, dict):
                    output.append(str(value))
                else:
                    output.append(str(value["name"]))
            _click.echo(",".join(output))
    else:
        for script in data:
            _click.echo(script["name"])


# @script.command()
