# -*- coding: utf-8 -*-

import json as _json

import requests as _requests
import click as _click

import taskmanager.models.schemas as _schema
import taskmanager.commands.base as _base

@_click.group(short_help="command to get/create/update teams")
def team():
    pass


@team.command(short_help="Get all teams")
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
        "{{server}}/teams?{params}".format(
            params=params,
        ),
    )
    if not result:
        return
    result = result.json()
    result.pop("meta")
    data = _schema.Team().load(result, many=True)
    if format == "json":
        _click.echo(_json.dumps(data))
    elif format == "csv":
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
    params = {
        'name': name,
    }
    params = _schema.Team().dump(params).data
    result = _base.post_response(
        "{server}/teams",
        data=_json.dumps(params)
    )
    if not result:
        return
    _click.echo("Add new team")


@team.command(short_help="Update team")
@_click.argument("team_id")
@_click.argument("name")
def update(team_id, name):
    result = _base.patch_response(
        "{{server}}/teams/{team_id}".format(
            team_id=team_id,
        ),
        data=_json.dumps({"name": name})
    )
    if not result:
        return

    _click.echo("Team updated.")
