# -*- coding: utf-8 -*-

import sqlalchemy as _sa
import sqlalchemy.orm as _orm

from .meta import Base


class Team(Base):
    """ Team mapper class """
    __tablename__ = 'teams'
    id = _sa.Column(_sa.Integer, primary_key=True)
    name = _sa.Column(_sa.Text)


class Script(Base):
    """ Script mapper class """
    __tablename__ = 'scripts'
    id = _sa.Column(_sa.Integer, primary_key=True)
    name = _sa.Column(_sa.Text, index=True)
    script = _sa.Column(_sa.Text, index=True)
    team_id = _sa.Column(_sa.Integer, _sa.ForeignKey('teams.id'), index=True)
    team = _orm.relationship('Team', backref='scripts')
    status = _sa.Column(_sa.Text)


class Worker(Base):
    """ Worker mapper class"""
    __tablename__ = 'workers'
    id = _sa.Column(_sa.Integer, primary_key=True)
    name = _sa.Column(_sa.Text, index=True)
    state = _sa.Column(_sa.Text)

    def is_online(self):
        """ check if worker is online """
        return self.state == 'ONLINE'


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
    # task_id = association_table.c.task_id
    # depend_id = association_table.c.depend_id
    # __table_args__ = (
    #     _sa.UniqueConstraint('task_id', 'depend_id', name='unique_friendships'),
    # )


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
        _sa.ForeignKey('workers.id'),
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
    worker = _orm.relationship('Worker', backref='tasks')
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

    task = _orm.relationship(
        'Task',
        backref='logs'
    )
