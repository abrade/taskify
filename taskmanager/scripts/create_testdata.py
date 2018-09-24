#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys as _sys
import logging as _logging
import contextlib as _ct
import datetime as _dt
import time as _time

import click as _click

import pyramid.paster as _paster

import sqlalchemy.orm as _orm

import taskmanager.models as _models
import taskmanager.views as _views

_log = _logging.getLogger(__name__)


@_ct.contextmanager
def session(settings):
    engine = _models.get_engine(settings)
    session_factory = _models.get_session_factory(engine)
    db_session = _orm.scoped_session(session_factory)
    yield db_session
    db_session.remove()
    engine.dispose()


class TestDataHelper(object):
    def __init__(self, settings):
        self.settings = settings

    def _add_object(self, obj):
        with session(self.settings) as db:
            db.add(obj)
            db.commit()
            db.refresh(obj)

    def create_team(self, name):
        team = _models.Team(name)
        self._add_object(team)
        return team

    def create_script(self, *args, **argv):
        script = _models.Script(*args, **argv)
        self._add_object(script)
        return script

    def create_worker(self, name, state="ONLINE"):
        worker = _models.Worker(name, state=state)
        self._add_object(worker)
        return worker

    def create_queue(self, name, state="active"):
        queue = _models.WorkerQueue(name, state=state)
        self._add_object(queue)
        return queue

    def create_task(self, *args, **argv):
        task = _models.Task(*args, **argv)
        self._add_object(task)
        return task

    def add_dependency(self, task_id, depends_on_id):
        task_depends = _models.TaskDepends(
            task_id,
            depends_on_id,
        )
        self._add_object(task_depends)
        return task_depends

    def create_tasklog(self, *args, **argv):
        task_log = _models.TaskLog(*args, **argv)
        self._add_object(task_log)
        return task_log


class TaskBuilder(object):
    def __init__(self, settings):
        self.settings = settings
        self.helper = TestDataHelper(settings)
        self.queue = None
        self.worker = None
        self.script = None
        self.task = None
        self.team = None

    def create_script(
            self,
            name,
            cmd,
            status,
            type_=_models.Script.SCRIPT_TYPE,
            default_options=None,
    ):
        self.script = self.helper.create_script(
            name,
            cmd,
            self.team.id,
            status,
            type=type_,
            default_options=default_options,
        )
        return self

    def with_script(self, script_id):
        with session(self.settings) as db:
            self.script = db.query(
                _models.Script
            ).get(script_id)
        return self

    def create_worker(self, name, status="ONLINE"):
        self.worker = self.helper.create_worker(name, status)
        return self

    def with_worker(self, worker_id):
        with session(self.settings) as db:
            self.worker = db.query(
                _models.Worker
            ).get(worker_id)
        return self

    def create_team(self, team_name):
        self.team = self.helper.create_team(team_name)
        return self

    def with_team(self, team_id):
        with session(self.settings) as db:
            self.team = db.query(
                _models.Team
            ).get(team_id)
        return self

    def create_queue(self, name, status="active"):
        self.queue = self.helper.create_queue(name, status)
        return self

    def with_queue(self, queue_id):
        with session(self.settings) as db:
            self.queue = db.query(
                _models.WorkerQueue
            ).get(queue_id)
        return self

    def create_task(
            self,
            title,
            state,
            parent_id=None,
            options=None,
            scheduled_by="",
    ):
        if not options:
            options = self.script.default_options

        self.task = self.helper.create_task(
            title,
            self.script.id,
            self.queue.id,
            parent_id,
            state,
            options,
            scheduled_by=scheduled_by,
        )
        return self

    def with_task(self, task_id):
        with session(self.settings) as db:
            self.task = db.query(
                _models.Task
            ).get(task_id)
        return self

    def create_tasklog(self, run, state):
        self.helper.create_tasklog(
            self.task.id,
            run,
            state,
            self.worker.id,
        )
        return self

    def with_dependency(self, task_id):
        self.helper.add_dependency(self.task.id, task_id)
        return self


@_click.command()
@_click.argument("config", required=True)
def test_data(config):
    # scripts
    # worker
    # queue
    # tasks
    # task_logs -> started, succeed
    # task_logs -> started, failed, started, succeed
    # task_logs -> started, failed, started, failed, failed-ack

    _paster.setup_logging(config)
    settings = _paster.get_appsettings(config)
    builder1 = TaskBuilder(settings)
    run = _dt.datetime.now()
    builder1.create_team(
        "A-Team"
    ).create_script(
        "short_script",
        "test_run",
        "ACTIVE",
        default_options={"TIMEOUT": "1"},
    ).create_queue(
        "default"
    ).create_worker(
        "default@localhost"
    ).create_task(
        "ftl script",
        "SUCCEED",
    ).create_tasklog(
        run,
        "STARTED",
    ).create_tasklog(
        run + _dt.timedelta(seconds=1),
        "SUCCEED",
    )
    builder2 = TaskBuilder(settings)
    run = _dt.datetime.now()
    builder2.create_team(
        "B-Team"
    ).create_script(
        "slow_script",
        "test_run",
        "ACTIVE",
        default_options={"TIMEOUT": "30"},
    ).with_queue(
        builder1.queue.id
    ).with_worker(
        builder1.worker.id
    ).create_task(
        "normal scripting",
        "SUCCEED",
    ).create_tasklog(
        run,
        "STARTED"
    ).create_tasklog(
        run + _dt.timedelta(seconds=10),
        "RETRIED",
    ).create_tasklog(
        run + _dt.timedelta(minutes=5),
        "STARTED",
    ).create_tasklog(
        run + _dt.timedelta(minutes=5, seconds=30),
        "SUCCEED",
    )

    builder3 = TaskBuilder(settings)
    builder3.with_team(
        builder1.team.id
    ).create_script(
        "slow_script",
        "test_run",
        "ACTIVE",
        default_options={"TIMEOUT": "30"},
    ).create_queue(
        "worker1"
    ).create_worker(
        "worker1@localhost"
    ).create_task(
        "slooooooow script",
        "SUCCEED",
    ).with_dependency(
        builder1.task.id
    ).create_tasklog(
        run + _dt.timedelta(hours=1),
        "STARTED",
    ).create_tasklog(
        run + _dt.timedelta(hours=1, minutes=1),
        "SUCCEED",
    )

    builder4 = TaskBuilder(settings)
    builder4.with_team(
        builder3.team.id
    ).create_script(
        "failure_script",
        "test_run",
        "ACTIVE",
        default_options={"TIMEOUT": "20", "ABORT": "True"},
    ).with_queue(
        builder3.queue.id
    ).with_worker(
        builder3.worker.id
    ).create_task(
        "failed script",
        "FAILED",
        parent_id=builder3.task.id,
    ).create_tasklog(
        run + _dt.timedelta(minutes=23),
        "STARTED",
    ).create_tasklog(
        run + _dt.timedelta(minutes=24),
        "RETRIED",
    ).create_tasklog(
        run + _dt.timedelta(minutes=25),
        "STARTED",
    ).create_tasklog(
        run + _dt.timedelta(minutes=26),
        "RETRIED",
    ).create_tasklog(
        run + _dt.timedelta(minutes=27),
        "STARTED",
    ).create_tasklog(
        run + _dt.timedelta(minutes=28),
        "FAILED",
    )

    builder5 = TaskBuilder(settings)
    builder5.with_team(
        builder4.team.id
    ).create_script(
        "run_func",
        "taskmanager.scripts.test_function.simulate_function",
        "ACTIVE",
        type_=_models.Script.FUNC_TYPE,
        default_options={"timeout": "5", "abort": "False"},
    ).with_queue(
        builder4.queue.id
    ).with_worker(
        builder4.worker.id
    ).create_task(
        "run_func",
        "PRERUN",
    )


def main(_argv=tuple(_sys.argv)):
    test_data()
