# -*- coding:utf-8 -*-

import json as _json
import platform as _platform

import requests as _requests
import click as _click

import taskmanager.models.schemas as _schema
import taskmanager.commands.base as _base

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
    url = "{{server}}/workerqueues/name/{queue_name}".format(
        queue_name=queue_name,
    )
    try:
        result = _base.get_response(url)
    except _json.JSONDecodeError:
        return None
    if not result:
        return
    result = result.json()
    result = result.pop("data")
    return _schema.WorkerQueue().load(result)


def _get_script_by_name(script_name):
    url = "{{server}}/scripts/name/{script_name}".format(
        script_name=script_name,
    )
    try:
        result = _base.get_response(url)
    except _json.JSONDecodeError:
        return None
    if not result:
        return
    result = result.json()
    result = result.pop("data")
    return _schema.Script().load(result)


# def _get_remote_data(task, url, data_type, schema):
#     url = "{{server}}/{url}/{script}".format(
#         script=task[data_type],
#         url=url,
#     )
#     result = _base.get_response(url)
#     if not result:
#         return

#     return schema().load(result.json()).data


def _get_remote_data(url, schema):
    url = "{{server}}{url}".format(url=url)
    result = _base.get_response(url)
    if not result:
        return
    result = result.json()
    if 'data' in result:
        result = result.pop("data")
    return schema().load(result)


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

    url = "{{server}}/tasks?{params}".format(
        params="&".join(params),
    )

    response = _base.get_response(url)
    if not response:
        return
    result = response.json()
    meta = result.pop("meta")
    attrs = {'many': True}
    json_api = result.get('json_api', False)
    if json_api:
        attrs['include_data'] = ("script", "worker", "script.team", "depends")
    else:
        result = result.pop("data")
    data = _schema.Tasks(**attrs).load(result)
    if not json_api:
        for task in data:
            task["script"] = _get_remote_data(task["script"], _schema.Script)
            task["script"]["team"] = _get_remote_data(task["script"]["team"], _schema.Team)
            task["worker"] = _get_remote_data(task["worker"], _schema.WorkerQueue)

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
    params = _schema.Tasks().dump(params)
    result = _base.post_response(
        "{server}/tasks",
        data=_json.dumps(params)
    )

    if not result:
        return
    result = result.json()
    _click.secho("{id}".format(**result), fg="green")


@task.command(short_help="Get result for task")
@_click.argument("task_id")
def result(task_id):
    result = _base.get_response(
        "{{server}}/tasks/{task_id}/result".format(
            task_id=task_id,
        )
    )
    if not result:
        return
    result = result.json()
    data = result["data"]
    _click.echo("Result Code: {return_code}".format(**data))
    _click.secho("Stdout: {stdout}".format(**data), fg="green")
    _click.secho("Stderr: {stderr}".format(**data), fg="red")
