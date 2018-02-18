# -*- coding: utf-8 -*-

import json as _json

import requests as _requests
import click as _click

from .config import get_config

import taskmanager.models.schemas as _schema


@_click.group(short_help="command to get/create/update teams")
def team():
    pass


@team.command(short_help="Get all teams")
@_click.option("--json", is_flag=True)
@_click.option("--csv", is_flag=True)
def list(json, csv):
    cfg = get_config()
    result = _requests.get(
        "{server}/teams".format(**cfg),
    ).json()
    if result["result"] != "OK":
        _click.echo("Couldn't receive data. Error: {error}".format(**result))
        return
    data = _schema.Team().load(result, many=True).data
    if json:
        _click.echo(_json.dumps(data))
    elif csv:
        _click.echo(",".join(data[0].keys()))
        for team in data:
            _click.echo(
                ",".join(
                    str(v) for v in team.values()
                )
            )
    else:
        for team in data:
            _click.echo(team["name"])


@team.command(short_help="Add new team")
@_click.argument("name")
def add(name):
    cfg = get_config()
    result = _requests.post(
        "{server}/teams".format(**cfg),
        data=_json.dumps({"name": name})
    ).json()
    if result["result"] != "OK":
        _click.echo("Couldn't receive data. Error: {error}".format(**result))
        return
    _click.echo("Add new team")


@team.command(short_help="Update team")
@_click.argument("team_id")
@_click.argument("name")
def update(team_id, name):
    cfg = get_config()
    result = _requests.patch(
        "{server}/teams/{team_id}".format(
            team_id=team_id,
            **cfg
        ),
        data=_json.dumps({"name": name})
    ).json()
    if result["result"] != "OK":
        _click.echo("Couldn't update team. Error: {error}".format(**result))
        return

    _click.echo("Team updated.")
