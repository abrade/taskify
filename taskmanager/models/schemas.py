# -*- coding: utf-8 -*-

import marshmallow_sqlalchemy as _marshmallow
import marshmallow.fields as _fields


class Team(_marshmallow.ModelSchema):
    id = _fields.Integer()
    name = _fields.Str()


class Worker(_marshmallow.ModelSchema):
    id = _fields.Integer()
    name = _fields.Str()
    state = _fields.Str()


class Script(_marshmallow.ModelSchema):
    id = _fields.Integer()
    name = _fields.Str()
    script = _fields.Str()
    status = _fields.Str()
    team = _fields.Nested("Team")

class ParentTask(_marshmallow.ModelSchema):
    id = _fields.Integer()
    scheduled = _fields.DateTime()
    run = _fields.DateTime()
    state = _fields.Str()
    locks = _fields.Str()
    options = _fields.Dict()
    worker = _fields.Nested("Worker")


class Tasks(_marshmallow.ModelSchema):
    id = _fields.Integer()
    scheduled = _fields.DateTime()
    run = _fields.DateTime()
    state = _fields.Str()
    locks = _fields.Str()
    options = _fields.Dict()
    worker = _fields.Nested("Worker")
    depends = _fields.Nested("TaskDepend")
    parent = _fields.Nested("ParentTask")
    script = _fields.Nested("Script")
    logs = _fields.List(_fields.Nested("TaskLog"))


class TaskDepend(_marshmallow.ModelSchema):
    task_id = _fields.Integer()


class TaskLog(_marshmallow.ModelSchema):
    task_id = _fields.Integer()
    run = _fields.DateTime()
    state = _fields.Str()
