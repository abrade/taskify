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


def _start_task(task, config):
    params = [task.script.cmd, config, task.options]
    additional_info = {}
    if task.parent:
        additional_info["parent_id"] = task.parent.id
    task_run = _views.start_task.apply_async(
        args=tuple(params),
        kwargs={"additional_info": additional_info},
        task_id=str(task.id),
        routing_key=task.worker.name,
        queue=task.worker.name,
    )
    task.run = _dt.datetime.utcnow()
    return task_run


def _start_function(task, config):
    params = [task.script.cmd, config, task.options]
    additional_info = {}
    if task.parent:
        additional_info["parent_id"] = task.parent.id
    task_run = _views.start_function.apply_async(
        args=params,
        kwargs={"additional_info": additional_info},
        task_id=str(task.id),
        routing_key=task.worker.name,
        queue=task.worker.name,
    )
    task.run = _dt.datetime.utcnow()
    return task_run


def _handle_failed_tasks(session_factory, config):
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
                diff = None
            if diff is None or diff > _dt.timedelta(minutes=5):
                if task.script.is_script():
                    task_run = _start_task(task, config)
                _log.info("Restart failed task %r", task_run.id)


def _check_parent(task):
    if task.parent is None:
        return True

    if task.parent.state == "SUCCEED":
        return True

    return False


def _handle_prerun_tasks(session_factory, config):
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

            if _check_parent(task):
                depends_state = [
                    (depend_task.id, depend_task.state)
                    for depend_task in task.depends
                    if depend_task.state != "SUCCEED"
                ]
                _log.info(
                    "Depends {} - {}".format(
                        depends_state,
                        [
                            (depend_task.id, depend_task.state)
                            for depend_task in task.depends
                        ],
                    )
                )
                if not depends_state:
                    if task.script.is_script():
                        task_run = _start_task(task, config)
                    elif task.script.is_function():
                        task_run = _start_function(task, config)

                    if task.parent:
                        log_str = "Start Task {} after parent {}".format(
                            task.id,
                            task.parent.id,
                        )
                        _log.info(log_str)
                    else:
                        _log.info(
                            "Start Task '{}' ({})".format(
                                task.id,
                                task.script.type,
                            )
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
    _log.info("Scheduler up and running...")
    while True:
        _handle_prerun_tasks(session_factory, config)
        _handle_failed_tasks(session_factory, config)
        _time.sleep(waittime)


def main(argv=tuple(_sys.argv)):
    scheduler()
