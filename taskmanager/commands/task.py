# -*- coding:utf-8 -*-

import json as _json
import platform as _platform

import requests as _requests
import click as _click

from .config import get_config

import taskmanager.models.schemas as _schema

_COLORS = {
    "SUCCEED": "green",
    "FAILED": "red",
    "FAILED-ACKED": "magenta",
    "RETRIED": "yellow",
    "PRERUN": "blue",
    "STARTED": "cyan",
    "DELETED": "cyan",
}


def _get_worker_queue_by_name(queue_name):
    cfg = get_config()
    url = "{server}/workerqueues/name/{queue_name}".format(
        queue_name=queue_name,
        **cfg,
    )
    try:
        result = _requests.get(url).json()
    except _json.JSONDecodeError:
        return None
    if result["result"] != "OK":
        _click.secho(
            "Couldn't get result. Error: {error}".format(**result),
            fg="red",
        )
        return
    return _schema.WorkerQueue().load(result).data


def _get_script_by_name(script_name):
    cfg = get_config()
    url = "{server}/scripts/name/{script_name}?include_data=1".format(
        script_name=script_name,
        **cfg,
    )
    try:
        result = _requests.get(url).json()
    except _json.JSONDecodeError:
        return None
    if result["result"] != "OK":
        _click.secho(
            "Couldn't get result. Error: {error}".format(**result),
            fg="red",
        )
        return
    return _schema.Script().load(result).data


def _get_remote_data(task, url, data_type, schema):
    url = "{server}/{url}/{script}?include_data=1".format(
        script=task[data_type],
        url=url,
        **get_config()
    )
    result = _requests.get(url).json()
    if result["result"] != "OK":
        _click.secho("Couldn't get result. Error: {error}".format(
            **result),
            fg="red"
        )
        return

    return schema().load(result).data


@_click.group(short_help="command to get/create/update tasks")
def task():
    pass


@task.command(short_help="Get all tasks")
@_click.option(
    "--format",
    type=_click.Choice(["table", "json", "csv"]),
    default="table",
    help="Select output format (default: table)"
)
@_click.option("--team_id",  required=False, help="Filter by team id")
@_click.option("--script_id", required=False, help="Filter by script id")
@_click.option("--worker_id", required=False, help="Filter by worker id")
@_click.option("--state", required=False, default="ALL", help="Filter by state")
@_click.option("--size", required=False, default=100, help="Limit Items in result")
@_click.option("--page", required=False, default=0, help="Page for the result")
def list(format, team_id, script_id, worker_id, state, size, page):
    params = ["include_data=1"]
    if team_id:
        params.append(f"team={team_id}")
    if script_id:
        params.append(f"script={script_id}")
    if worker_id:
        params.append(f"worker={worker_id}")
    if state:
        params.append(f"state={state}")
    if size:
        params.append(f"page[size]={size}")
    if page:
        params.append(f"page[number]={page}")

    url = "{server}/tasks?{params}".format(
        params="&".join(params),
        **get_config()
    )

    result = _requests.get(url).json()
    if result["result"] != "OK":
        _click.secho("Couldn't get result. Error: {error}".format(
            **result), fg="red")
        return
    meta = result.pop("meta")
    data = _schema.Tasks(many=True).load(result)

    if format == "json":
        _click.echo(_json.dumps(data))
    elif format == "csv":
        _click.echo(",".join(data[0].keys()))
        for task in data:
            output = []
            for _key, value in task.items():
                if not isinstance(value, dict):
                    output.append(str(value))
                else:
                    output.append(str(value["name"]))
            _click.echo(",".join(output))
    else:
        format_string = "{task_id:>10} | {title:32} | {script:15} | {worker:10} | {scheduled:32} | {run:32} | {state:12} | {team:20}"
        line = "{task_id:>10}-+-{title:32}-+-{script:15}-+-{worker:10}-+-{scheduled:32}-+-{run:32}-+-{state:12}-+-{team:20}".format(
            task_id="-"*10,
            title="-"*32,
            script="-"*15,
            worker="-"*10,
            scheduled="-"*32,
            run="-"*32,
            state="-"*12,
            team="-"*20,
        )
        _click.echo(
            format_string.format(
                task_id="ID",
                title="Title",
                script="Script",
                worker="Worker",
                scheduled="Scheduled",
                run="Run",
                state="State",
                team="Team",
            )
        )
        _click.echo(line)
        for task in data:
            if task["run"]:
                run_time = task["run"].isoformat(' ')
            else:
                run_time = 'NOT RUNNING'

            if task["scheduled"]:
                schedule_time = task["scheduled"].isoformat(' ')
            else:
                schedule_time = 'NOT SCHEDULED'

            text_formatted = format_string.format(
                task_id=task["id"],
                title=task.get("title", ''),
                script=task["script"]["name"],
                worker=task["worker"]["name"],
                scheduled=schedule_time,
                run=run_time,
                state=task["state"] or 'UNKNOWN',
                team=task["script"]["team"]["name"],
            )
            _click.secho(text_formatted, fg=_COLORS[task["state"]])


@task.command(short_help="add new task")
@_click.argument("title")
@_click.argument("worker")
@_click.argument("script")
@_click.option("--option", multiple=True, nargs=2, type=_click.Tuple([str, str]), required=False)
@_click.option("--parent", type=int, required=False)
@_click.option("--depend", type=int, multiple=True, help="Task depending on Task ids", required=False)
def add(title, worker, script, option, parent, depend):
    cfg = get_config()
    worker_queue = _get_worker_queue_by_name(worker)
    if worker_queue is None:
        _click.secho(
            "Queue {worker!r} not found.".format(
                worker=worker
            ),
            fg="red",
        )
        return
    script_data = _get_script_by_name(script)
    if script_data is None:
        _click.secho(
            "Script {script!r} not found.".format(
                script=script
            ),
            fg="red",
        )
        return

    params = {
        "title": title,
        "worker": worker_queue,
        "script": script_data,
        "worker_id": worker_queue["id"],
        "script_id": script_data["id"],
        "options": {
            opt[0]: opt[1]
            for opt in option
        },
        "state": "PRERUN",
        "scheduledBy": _platform.node(),
        "depends": [],
    }
    if parent:
        params["parent_id"] = parent
    if depend:
        params["depends"] = depend
    # {"include_data": ("script", "worker",)}
    params = _schema.Tasks(include_data=("script", "worker")).dump(params).data
    result = _requests.post(
        "{server}/tasks".format(**cfg),
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
    _click.secho("{id}".format(**result), fg="green")


@task.command(short_help="Get result for task")
@_click.argument("task_id")
def result(task_id):
    cfg = get_config()
    result = _requests.get(
        "{server}/tasks/{task_id}/result".format(
            task_id=task_id,
            **cfg
        )
    ).json()
    if result["result"] != "OK":
        _click.secho("Couldn't get result. Error: {error}".format(
            **result), fg="red")
        return

    data = result["data"]
    _click.echo("Result Code: {return_code}".format(**data))
    _click.secho("Stdout: {stdout}".format(**data), fg="green")
    _click.secho("Stderr: {stderr}".format(**data), fg="red")
