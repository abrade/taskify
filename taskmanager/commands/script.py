# -*- coding:utf-8 -*-

import json as _json

import requests as _requests
import click as _click

from .config import get_config

import taskmanager.models.schemas as _schema
import taskmanager.commands.base as _base


def _get_team_by_name(team_name):
    cfg = get_config()
    url = "{{server}}/teams/name/{team_name}".format(
        team_name=team_name,
    )
    try:
        result = _base.get_response(url)
    except _json.JSONDecodeError:
        return None
    if not response:
        return
    return _schema.Team().load(result.json()).data


@_click.group(short_help="command to get/create/update scripts")
def script():
    pass


@script.command(short_help="Get all scripts")
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
        "{{server}}/scripts?{params}".format(
            params=params,
        ),
    )

    if not response:
        return
    result = response.json()
    result.pop("meta")
    data = _schema.Script(many=True).load(result)
    if format == "json":
        _click.echo(_json.dumps(data))
    elif format == "csv":
        _click.echo(",".join(data[0].keys()))
        for script in data:
            output = []
            for _key, value in script.items():
                output.append(str(value))
            _click.echo(",".join(output))
    else:
        for script in data:
            _click.echo(script["name"])


@script.command(short_help="Add a new script")
@_click.argument("name", type=str)
@_click.argument("cmd", type=str)
@_click.argument("team", type=str)
@_click.argument("options")
@_click.option(
    "--type",
    type=_click.Choice(["SCRIPT", "FUNCTION"]),
    default="SCRIPT",
    help="Set type of script",
)
def add(name, cmd, team, options, type):
    team = _get_team_by_name(team)
    if team is None:
        _click.secho(
            "Team {team!r} not found.".format(
                team=team
            ),
            fg="red",
        )
        return

    params = {
        "name": name,
        "cmd": cmd,
        "type": type,
        "status": "ACTIVE",
        "team_id": team["id"],
        "team": team,
        "default_options": options,
    }
    params = _schema.Script(include_data=("team",)).dump(params).data
    result = _base.post_response("{server}/scripts")
    if not result:
        return
    _click.secho("Script added.", fg="green")
