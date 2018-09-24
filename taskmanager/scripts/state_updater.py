#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging as _logging
import sys as _sys
import transaction as _tm
import datetime as _dt
import functools as _ft

import click as _click

import pyramid.paster as _paster

import taskmanager.models as _models
import taskmanager.views as _views

_log = _logging.getLogger(__name__)


_EVENT_TO_STATE = {
    "task-started": "STARTED",
    "task-succeeded": "SUCCEED",
    "task-failed": "FAILED",
    # "task-rejected": "REJECT",
    "task-retried": "RETRIED",
}

_HOSTNAME_TO_NAME = {}


def _worker_events(state, capp, session_factory, event):
    state.event(event)
    hostname = event["hostname"]
    inspect = capp.control.inspect(destination=[hostname])
    active_queue = inspect.active_queues()
    if not active_queue:
        if hostname not in _HOSTNAME_TO_NAME:
            return
        name = _HOSTNAME_TO_NAME[hostname]
    else:
        active_queue = active_queue[hostname][0]
        name = active_queue["name"]
        _HOSTNAME_TO_NAME[hostname] = name

    with _tm.manager:
        dbsession = _models.get_tm_session(session_factory, _tm.manager)
        worker_queue = dbsession.query(
            _models.WorkerQueue
        ).filter(
            _models.WorkerQueue.name == name
        ).first()

        worker = dbsession.query(
            _models.Worker
        ).filter(
            _models.Worker.name == hostname
        ).first()

        if not worker_queue:
            worker_queue = _models.WorkerQueue(name)
            dbsession.add(worker_queue)
            _log.info(
                "New Queue created {}".format(
                    worker_queue.name,
                )
            )

        if worker_queue.state != 'active':
            _log.info(
                "Queue {}: {} -> active".format(
                    worker_queue.name,
                    worker_queue.state,
                )
            )
            worker_queue.state = 'active'

        if not worker:
            worker = _models.Worker(hostname, "OFFLINE")
            dbsession.add(worker)

        if event["type"] in ("worker-heartbeat", "worker-online"):
            if worker.state != "ONLINE":
                worker.state = "ONLINE"
                _log.info("Worker {} -> ONLINE".format(worker.name))
        elif event["type"] in ("worker-offline",):
            if worker.state != "OFFLINE":
                worker.state = "OFFLINE"
                _log.info("Worker {} -> OFFLINE".format(worker.name))


def _task_events(state, session_factory, event):
    state.event(event)
    task_id = event["uuid"]
    with _tm.manager:
        try:
            int(task_id)
        except ValueError:
            _log.info("ID is not a integer {}".format(task_id))
            return
        dbsession = _models.get_tm_session(session_factory, _tm.manager)
        task = dbsession.query(_models.Task).get(task_id)
        event_type = event["type"]
        task_state = _EVENT_TO_STATE.get(event_type)
        if task_state == "STARTED":
            task.run = _dt.datetime.utcnow()

        _log.info(
            "Task {} [{:7} -> {}] @ {}".format(
                task.id,
                task.state,
                task_state,
                event['hostname']
            )
        )

        if task_state:
            task.state = task_state

        worker = dbsession.query(
            _models.Worker
        ).filter(
            _models.Worker.name == event["hostname"]
        ).one()
        log_entry = _models.TaskLog(
            task.id,
            _dt.datetime.utcnow(),
            task.state,
            worker.id,
        )
        log_entry.task = task
        log_entry.worker = worker
        dbsession.add(log_entry)


@_click.command()
@_click.argument('config', required=True)
def state_updater(config):
    _paster.setup_logging(config)
    settings = _paster.get_appsettings(config)

    engine = _models.get_engine(settings)
    session_factory = _models.get_session_factory(engine)

    capp = _views.celery_app
    state = capp.events.State()

    with _views.celery_app.connection() as connection:
        worker_events = _ft.partial(
            _worker_events,
            state,
            capp,
            session_factory,
        )
        task_events = _ft.partial(
            _task_events,
            state,
            session_factory,
        )
        recv = _views.celery_app.events.Receiver(connection, handlers={
            "worker-online": worker_events,
            "worker-offline": worker_events,
            "worker-heartbeat": worker_events,
            "task-started": task_events,
            "task-succeeded": task_events,
            "task-failed": task_events,
            "task-rejected": task_events,
            "task-retried": task_events,
        })
        recv.capture(limit=None, timeout=None, wakeup=True)


def main(argv=tuple(_sys.argv)):
    state_updater()
