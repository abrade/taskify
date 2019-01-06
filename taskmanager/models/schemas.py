# -*- coding: utf-8 -*-

import marshmallow as _mm
import marshmallow_jsonapi as _marshmallow
import marshmallow_jsonapi.fields as _fields

SimpleSchema = _mm.Schema
Schema = _marshmallow.Schema


class Team(Schema):
    id = _fields.Integer()
    name = _fields.Str()

    class Meta:
        type_ = "teams"
        strict = True


class Worker(Schema):
    id = _fields.Integer()
    name = _fields.Str()
    state = _fields.Str()

    class Meta:
        type_ = "workers"
        strict = True


class WorkerQueue(Schema):
    id = _fields.Integer()
    name = _fields.Str()
    state = _fields.Str()

    class Meta:
        type_ = "workerqueues"
        strict = True


class Script(Schema):
    id = _fields.Integer()
    name = _fields.Str()
    cmd = _fields.Str()
    status = _fields.Str()
    team = _fields.Relationship(
        "/teams/{team_id}",
        include_data=True,
        schema="Team",
        type_="teams",
        related_url_kwargs={"team_id": "<team_id>"},
    )
    team_id = _fields.Int()
    type = _fields.Str()
    default_options = _fields.Dict(
        allow_none=True,
    )

    class Meta:
        type_ = "scripts"
        strict = True


class ParentTask(Schema):
    id = _fields.Integer()
    title = _fields.Str(default="")
    scheduled = _fields.DateTime()
    run = _fields.DateTime()
    state = _fields.Str()
    locks = _fields.Str()
    options = _fields.Dict()
    worker = _fields.Relationship(
        "/workerqueues/{worker_id}",
        include_data=True,
        schema="WorkerQueue",
        type_="workerqueues",
        related_url_kwargs={"worker_id": "<worker_id>"},
    )

    class Meta:
        type_ = "tasks"
        strict = True


class TaskDepend(SimpleSchema):
    id = _fields.Integer(load_from="task_id")

    class Meta:
        type_ = "taskdepend"


class Tasks(Schema):
    id = _fields.Integer()
    scheduled = _fields.DateTime(format="%a, %d %b %Y %H:%M:%S")
    run = _fields.DateTime(format="%a, %d %b %Y %H:%M:%S", allow_none=True)
    title = _fields.Str(default="")
    state = _fields.Str()
    locks = _fields.Str(allow_none=True)
    options = _fields.Dict()
    scheduled_by = _fields.Str(
        load_from="scheduledBy",
        dump_to="scheduledBy",
    )
    worker = _fields.Relationship(
        "/workerqueues/{worker_id}",
        include_data=True,
        schema="WorkerQueue",
        type_="workerqueues",
        related_url_kwargs={"worker_id": "<worker_id>"},
    )

    depends = _fields.Relationship(
        "/tasks/{task_id}/depends",
        related_url_kwargs={"task_id": "<id>"},
        schema="Tasks",
        many=True,
    )

    parent = _fields.Relationship(
        "/tasks/{task_id}",
        related_url_kwargs={"task_id": "<parent_id>"},
        schema="ParentTask",
    )

    children = _fields.Relationship(
        "/tasks/{task_id}/children",
        many=True,
        schema="Task",
        related_url_kwargs={"task_id": "<id>"}
    )

    script = _fields.Relationship(
        "/scripts/{script_id}",
        include_data=True,
        schema="Script",
        type_="scripts",
        related_url_kwargs={"script_id": "<script_id>"},
    )

    logs = _fields.Relationship(
        "/tasks/{task_id}/logs",
        include_data=True,
        many=True,
        type_='tasklog',
        related_url_kwargs={"task_id": "<id>"},
    )

    class Meta:
        type_ = "tasks"
        strict = True


class TaskLog(Schema):
    id = _fields.Integer()
    task_id = _fields.Integer()
    run = _fields.DateTime(format="%a, %d %b %Y %H:%M:%S")
    state = _fields.Str()
    worker = _fields.Relationship(
        "/workers/{worker_id}",
        include_data=True,
        schema="Worker",
        type_="workers",
        related_url_kwargs={'worker_id': '<worker_id>'}
    )

    class Meta:
        type_ = "tasklog"
        strict = True


class WorkerOptions(Schema):
    id = _fields.Integer()
    concurrency = _fields.Integer()
    prefetchcount = _fields.Integer()
    statistics = _fields.Dict()

    class Meta:
        type_ = "workeroptions"
        strict = True
