# -*- coding: utf-8 -*-

#import marshmallow_sqlalchemy as _marshmallow
import marshmallow_jsonapi as _marshmallow
import marshmallow_jsonapi.fields as _fields


class Team(_marshmallow.Schema):
    id = _fields.Integer()
    name = _fields.Str()

    class Meta:
        type_ = "team"
        strict = True


class Worker(_marshmallow.Schema):
    id = _fields.Integer()
    name = _fields.Str()
    state = _fields.Str()

    class Meta:
        type_ = "worker"
        strict = True


class WorkerQueue(_marshmallow.Schema):
    id = _fields.Integer()
    name = _fields.Str()
    state = _fields.Str()

    class Meta:
        type_ = "workerqueue"
        strict = True


class Script(_marshmallow.Schema):
    id = _fields.Integer()
    name = _fields.Str()
    cmd = _fields.Str()
    status = _fields.Str()
    #team = _fields.Nested("Team")
    team = _fields.Relationship(
        "/teams/{team_id}",
        include_data=True,
        schema="Team",
        related_url_kwargs={"team_id": "<team_id>"},
    )
    type = _fields.Str()

    class Meta:
        type_ = "script"
        strict = True


class ParentTask(_marshmallow.Schema):
    id = _fields.Integer()
    title = _fields.Str(default="")
    scheduled = _fields.DateTime()
    run = _fields.DateTime()
    state = _fields.Str()
    locks = _fields.Str()
    options = _fields.Dict()
    worker = _fields.Nested("Worker")

    class Meta:
        type_ = "task"
        strict = True


class Tasks(_marshmallow.Schema):
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
        related_url_kwargs={"worker_id": "<worker_id>"},
    )
    depends = _fields.Nested(
        "TaskDepend",
        many=True,
        allow_none=True,
        default=None
    )
    # depends = _fields.Relationship(
    #     "/tasks/{task_id}",
    #     related_url_kwargs={"task_id": "<depend_ids>"}
    # )

    parent = _fields.Relationship(
        "/tasks/{task_id}",
        related_url_kwargs={"task_id": "<parent_id>"},
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
        related_url_kwargs={"script_id": "<script_id>"},
    )

    logs = _fields.Relationship(
        "/tasklogs/{task_id}",
        include_data=True,
        many=True,
        schema="TaskLog",
        type_='tasklog',
        related_url_kwargs={"task_id": "<id>"},
    )

    class Meta:
        type_ = "task"
        strict = False


class TaskDepend(_marshmallow.Schema):
    id = _fields.Integer(load_from="task_id")

    class Meta:
        type_ = "taskdepend"
        strict = True


class TaskLog(_marshmallow.Schema):
    id = _fields.Integer()
    task_id = _fields.Integer(dump_to="taskId", load_from="taskId")
    run = _fields.DateTime(format="%a, %d %b %Y %H:%M:%S")
    state = _fields.Str()
    worker = _fields.Relationship(
        "/workers/{worker_id}",
        include_data=True,
        schema="Worker",
        type_="worker",
        related_url_kwargs={'worker_id': '<worker_id>'}
    )

    class Meta:
        type_ = "tasklog"
        strict = True


class WorkerOptions(_marshmallow.Schema):
    id = _fields.Integer()
    concurrency = _fields.Integer()
    prefetchcount = _fields.Integer()
    statistics = _fields.Dict()

    class Meta:
        type_ = "workeroptions"
        strict = True
