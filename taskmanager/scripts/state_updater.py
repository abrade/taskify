#/usr/bin/env python
# -*- coding: utf-8 -*-

import logging as _logging
import sys as _sys
import transaction as _tm
import datetime as _dt

import click as _click

import pyramid.paster as _paster

import taskmanager.models as _models
import taskmanager.views as _views

_log = _logging.getLogger(__name__)


@_click.command()
@_click.argument('config', required=True)
def state_updater(config):
    _paster.setup_logging(config)
    settings = _paster.get_appsettings(config)

    engine = _models.get_engine(settings)
    session_factory = _models.get_session_factory(engine)

    capp = _views.celery_app
    state = capp.events.State()
    hostname_to_name = {}
    def worker_events(event):
        state.event(event)
        hostname = event["hostname"]
        inspect = capp.control.inspect(destination=[hostname])
        active_queue = inspect.active_queues()
        if not active_queue:
            if hostname not in hostname_to_name:
                return
            name = hostname_to_name[hostname]
        else:
            active_queue = active_queue[hostname][0]
            name = active_queue["name"]
            hostname_to_name[hostname] = name

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
                _log.info(f"New Queue created {worker_queue.name}")
            elif worker_queue.state != 'active':
                _log.info(f"Queue {worker_queue.name}: {worker_queue.state} -> active")
                worker_queue.state = 'active'
            if not worker:
                worker = _models.Worker(hostname, "OFFLINE")
                dbsession.add(worker)
            if event["type"] in ("worker-heartbeat", "worker-online") and worker.state != "ONLINE":
                worker.state = "ONLINE"
                _log.info(f"Worker {worker.name} -> ONLINE")
            elif event["type"] in ("worker-offline",) and worker.state != "OFFLINE":
                worker.state = "OFFLINE"
                _log.info(f"Worker {worker.name} -> OFFLINE")

    def task_events(event):
        state.event(event)
        task_id = event["uuid"]
        with _tm.manager:
            try:
                _ = int(task_id)
            except ValueError:
                _log.info(f"ID is not a integer {task_id}")
                return
            dbsession = _models.get_tm_session(session_factory, _tm.manager)
            task = dbsession.query(_models.Task).get(task_id)
            event_type = event["type"]
            if event_type == "task-started":
                _log.info("Task %s [%-7s -> STARTED] @ %s", task.id, task.state, event['hostname'])
                task.state = "STARTED"
                task.run = _dt.datetime.utcnow()
            elif event_type == "task-succeeded":
                _log.info("Task %s [%-7s -> SUCCEED] @ %s", task.id, task.state, event['hostname'])
                task.state = "SUCCEED"
            elif event_type == "task-failed":
                _log.info("Task %s [%-7s -> FAILED] @ %s", task.id, task.state, event['hostname'])
                task.state = "FAILED"
            elif event_type == "task-rejected":
                #task.state = "REJECT"
                _log.info("REJECTED....")
            elif event_type == "task-retried":
                _log.info("Task %s [%-7s -> RETRIED] @ %s", task.id, task.state, event['hostname'])
                task.state = "RETRIED"
            log_entry = _models.TaskLog()
            log_entry.task_id = task.id
            log_entry.run = _dt.datetime.utcnow()
            log_entry.state = task.state
            log_entry.task = task
            dbsession.add(log_entry)

    with _views.celery_app.connection() as connection:
        #from ipdb import set_trace as br; br()

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
