# -*- coding: utf-8 -*-

import sqlalchemy as _sa
import sqlalchemy.orm as _orm

from .meta import Base


class Team(Base):
    """ Team mapper class """
    __tablename__ = 'teams'
    id = _sa.Column(_sa.Integer, primary_key=True)
    name = _sa.Column(_sa.Text)

    def __init__(self, name):
        self.name = name


class Script(Base):
    """ Script mapper class """
    SCRIPT_TYPE = "SCRIPT"
    FUNC_TYPE = "FUNCTION"

    __tablename__ = 'scripts'
    id = _sa.Column(_sa.Integer, primary_key=True)
    name = _sa.Column(_sa.Text, index=True)
    cmd = _sa.Column(_sa.Text, index=True)
    team_id = _sa.Column(_sa.Integer, _sa.ForeignKey('teams.id'), index=True)
    team = _orm.relationship('Team', backref='scripts')
    status = _sa.Column(_sa.Text)
    type = _sa.Column(_sa.Text, server_default=SCRIPT_TYPE)

    def __init__(self, name, cmd, team_id, status, type=SCRIPT_TYPE):
        self.name = name
        self.cmd = cmd
        self.team_id = team_id
        self.status = status
        self.type = type

    def is_script(self):
        return self.type == self.SCRIPT_TYPE

    def is_function(self):
        return self.type == self.FUNC_TYPE

class Worker(Base):
    """ Worker mapper class"""
    __tablename__ = 'workers'
    id = _sa.Column(_sa.Integer, primary_key=True)
    name = _sa.Column(_sa.Text, index=True)
    state = _sa.Column(_sa.Text)

    def __init__(self, name, state):
        self.name = name
        self.state = state

    def is_online(self):
        """ check if worker is online """
        return self.state == 'ONLINE'


class WorkerQueue(Base):
    """ Worker Queue mapper class"""
    __tablename__ = 'worker_queues'
    id = _sa.Column(_sa.Integer, primary_key=True)
    name = _sa.Column(_sa.Text, index=True)
    state = _sa.Column(_sa.Text, server_default="active")

    def __init__(self, name, state = "active"):
        self.name = name
        self.state = state

    def is_active(self):
        return self.state == "active"

association_table = _sa.Table(
    'task_dependencies', Base.metadata,
    _sa.Column(
        'task_id',
        _sa.BigInteger,
        _sa.ForeignKey('tasks.id'),
        primary_key=True
    ),
    _sa.Column(
        'depend_id',
        _sa.BigInteger,
        _sa.ForeignKey('tasks.id'),
        primary_key=True
    ),
    _sa.UniqueConstraint('task_id', 'depend_id', name='unique_friendships')
)

class TaskDepends(Base):
    __table__ = association_table

    def __init__(self, task_id, depend_id):
        self.task_id = task_id
        self.depend_id = depend_id

class Task(Base):
    """ Task mapper class """
    __tablename__ = 'tasks'
    id = _sa.Column(_sa.BigInteger, primary_key=True)
#    uuid = _sa.Column(_sa.Text, index=True)
    script_id = _sa.Column(
        _sa.Integer,
        _sa.ForeignKey('scripts.id'),
        index=True
    )
    worker_id = _sa.Column(
        _sa.Integer,
        _sa.ForeignKey('worker_queues.id'),
        index=True
    )
    scheduled = _sa.Column(
        _sa.DateTime,
        server_default=_sa.func.now()
    )
    run = _sa.Column(_sa.DateTime)
    state = _sa.Column(_sa.Text, index=True)
    locks = _sa.Column(_sa.Text)
    options = _sa.Column(_sa.JSON())
    parent_id = _sa.Column(
        _sa.BigInteger,
        _sa.ForeignKey('tasks.id'),
        index=True
    )

    script = _orm.relationship('Script', backref='tasks')
    worker = _orm.relationship('WorkerQueue', backref='tasks')
    parent = _orm.relationship(
        'Task',
        foreign_keys=parent_id,
        backref='children',
        remote_side='Task.id'
    )

    depends = _orm.relationship(
        'Task',
        secondary=association_table,
        primaryjoin=id == association_table.c.task_id,
        secondaryjoin=id == association_table.c.depend_id,
#        backref='depending'
    )

    def __init__(self, script_id, worker_id, parent_id, state, options):
        self.script_id = script_id
        self.worker_id = worker_id
        self.parent_id = parent_id
        self.state = state
        self.options = options


class TaskLog(Base):
    __tablename__ = 'task_log'
    task_id = _sa.Column(
        _sa.BigInteger,
        _sa.ForeignKey('tasks.id'),
        primary_key=True
    )
    run = _sa.Column(
        _sa.DateTime,
        primary_key=True,
        server_default=_sa.func.now()
    )
    state = _sa.Column(_sa.Text)
    worker_id = _sa.Column(
        _sa.Integer,
        _sa.ForeignKey("workers.id"),
    )

    task = _orm.relationship(
        'Task',
        backref='logs',
    )
    worker = _orm.relationship(
        "Worker",
        backref="task_runs",
    )
