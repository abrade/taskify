#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging as _logging
import sys as _sys
import transaction as _tm
import time as _time
import datetime as _dt

import click as _click

import pyramid.paster as _paster

import taskmanager.models as _models
import taskmanager.views as _views

_log = _logging.getLogger(__name__)


def _start_task(task):
    params = [task.script.cmd, task.options]
    task_run = _views.start_task.apply_async(
        tuple(params),
        task_id=str(task.id),
        routing_key=task.worker.name,
        queue=task.worker.name,
    )
    task.run = _dt.datetime.utcnow()
    return task_run


def _handle_failed_tasks(session_factory):
    with _tm.manager:
        session = _models.get_tm_session(session_factory, _tm.manager)
        tasks = session.query(
            _models.Task
        ).filter(
            _models.Task.state == 'FAILED'
        ).all()

        for task in tasks:
            if task.run:
                diff = _dt.datetime.utcnow() - task.run
            else:
                diff = _dt.timedelta(minutes=1)
            if diff > _dt.timedelta(minutes=5):
                if task.script.is_script():
                    task_run = _start_task(task)
                _log.info("Restart failed task %r", task_run.id)


def _handle_prerun_tasks(session_factory):
    with _tm.manager:
        session = _models.get_tm_session(session_factory, _tm.manager)
        tasks = session.query(
            _models.Task
        ).filter(
            _models.Task.run.is_(None)
        ).filter(
            _models.Task.state == 'PRERUN'
        ).all()
        for task in tasks:
            if not task.worker.is_active():
                continue

            if task.parent is None:
                depends_state = [
                    (depend_task.id, depend_task.state)
                    for depend_task in task.depends
                    if depend_task.state != "SUCCEED"
                ]
                _log.info(
                    f"Depends {depends_state}"
                )
                if not depends_state:
                    if task.script.is_script():
                        task_run = _start_task(task)
                    _log.info("Start Task %r", task_run.id)
            elif task.parent and task.parent.state == "SUCCEED":
                depends_state = [
                    (depend_task.id, depend_task.state)
                    for depend_task in task.depends
                    if depend_task.state != "SUCCEED"
                ]
                _log.info(
                    f"Depends {depends_state}"
                )
                if not depends_state:
                    if task.script.is_script():
                        task_run = _start_task(task)
                    _log.info(
                        f"Start Task {task_run.id} after parent {task.parent.id}"
                    )


@_click.command()
@_click.argument('config', required=True)
@_click.option(
    '--waittime',
    default=10,
    help='time to wait until check and start new tasks'
)
def scheduler(config, waittime):
    _paster.setup_logging(config)
    settings = _paster.get_appsettings(config)

    engine = _models.get_engine(settings)
    session_factory = _models.get_session_factory(engine)
    while True:
        _handle_prerun_tasks(session_factory)
        _handle_failed_tasks(session_factory)
        _time.sleep(waittime)


def main(argv=tuple(_sys.argv)):
    scheduler()
