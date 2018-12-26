# -*- coding: utf-8 -*-

import logging as _logging
import json as _json

import pyramid.view as _view

import taskmanager.views as _views
import taskmanager.models as _models
import taskmanager.models.schemas as _schemas

_log = _logging.getLogger(__name__)


class WorkerQueues(_views.BaseResource):
    NAME = "workerqueues"

    @_views.get_all()
    @_views.with_model(output_model=_schemas.WorkerQueue)
    def get_all(self, worker_id=None):
        queue_names = None
        with _views.dbsession(self.request) as session:
            if worker_id:
                worker = session.query(
                    _models.Worker
                ).get(worker_id)
                i = _views.celery_app.control.inspect([worker.name])
                worker_queues = i.active_queues()
                _log.info("Worker queues: {}".format(worker_queues))
                if worker_queues is None:
                    raise _views.RestAPIException(
                        "No worker_queues found",
                        _views.RESULT_NOTFOUND,
                    )
                if worker_queues and worker.name in worker_queues:
                    queue_names = [
                        queue["name"]
                        for queue in worker_queues[worker.name]
                    ]

            queues = session.query(
                _models.WorkerQueue
            )
            if queue_names:
                queues = queues.filter(
                    _models.WorkerQueue.name.in_(queue_names)
                )

            queues = queues.all()
            return queues

    @_views.post_one()
    @_views.with_model(model=_schemas.WorkerQueue)
    def post(self, post_data):
        queue_name = post_data.get("name")
        if queue_name is None:
            raise _views.RestAPIException(
                "No name is given",
                _views.RESULT_ERROR,
            )
        with _views.dbsession(self.request) as session:
            queue = _models.WorkerQueue(queue_name, "inaktive")
            session.add(queue)
            session.commit()
            session.refresh(queue)

            return queue

    @_views.get_one(param="worker_queue_id")
    @_views.with_model(output_model=_schemas.WorkerQueue)
    def get_one(self, worker_queue_id):
        with _views.dbsession(self.request) as session:
            queue = session.query(
                _models.WorkerQueue
            ).get(worker_queue_id)
            if queue is None:
                raise _views.RestAPIException(
                    f"Worker with id {worker_queue_id} not found",
                    _views.RESULT_NOTFOUND
                )
            return queue

    @_views.patch_one(param="worker_queue_id")
    @_views.with_model(model=_schemas.WorkerQueue)
    def update_one(self, worker_queue_id, post_data):
        queue_name = post_data.get('name')
        state = post_data.get('state')
        with _views.dbsession(self.request) as session:
            queue = session.query(
                _models.WorkerQueue
            ).get(worker_queue_id)
            if queue is None:
                raise _views.RestAPIException(
                    f"Worker with id {worker_queue_id} not found",
                    _views.RESULT_NOTFOUND
                )
            queue.name = queue_name
            queue.state = state
            session.commit()
            session.refresh(queue)
            return queue


@_view.view_defaults(route_name="name_queue")
class WorkerNameQueue(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET", renderer="json")
    def get_one(self):
        name = self.request.matchdict.get("name")
        with _views.dbsession(self.request) as session:
            queue = session.query(
                _models.WorkerQueue
            ).filter_by(name=name).all()
            print(queue)
            if queue is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Worker with id {name} not found",
                    "data": None,
                }
            return {
                "result": _views.RESULT_OK,
                **_schemas.WorkerQueue().dump(queue[0]).data,
            }


def includeme(config):
    WorkerQueues.init_handler(config)
    config.add_route("name_queue", "/workerqueues/name/:name")
