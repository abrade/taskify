# -*- coding: utf-8 -*-

import logging as _logging
import json as _json

import pyramid.view as _view

import taskmanager.views as _views
import taskmanager.models as _models
import taskmanager.models.schemas as _schemas

_log = _logging.getLogger(__name__)


@_view.view_defaults(route_name="all_queues")
class WorkerQueues(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET", renderer="json")
    def get_all(self):
        worker_id = self.request.params.get("worker_id")
        queue_names = None
        with _views.dbsession(self.request) as session:
            if worker_id:
                worker = session.query(
                    _models.Worker
                ).get(worker_id)
                i = _views.celery_app.control.inspect([worker.name])
                worker_queues = i.active_queues()
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
            queues = _schemas.WorkerQueue(
                many=True
            ).dump(
                queues
            )
            _log.info(queues)
            return {
                "result": _views.RESULT_OK,
                **queues.data,
            }

    @_view.view_config(request_method="POST", renderer="json")
    def post(self):
        # worker_name = self.request.params.get("name")
        _log.debug("Body: %s", self.request.body)
        try:
            data = self.request.json
            _log.debug("Data: %s", data)
        except _json.decoder.JSONDecodeError as decode_error:
            return {
                "result": _views.RESULT_ERROR,
                "error": decode_error.msg,
                "data": None,
            }
        queue_name = data.get("name")
        if queue_name is None:
            return {
                "result": _views.RESULT_ERROR,
                "error": "No name is given",
                "data": None,
            }
        with _views.dbsession(self.request) as session:
            queue = _models.WorkerQueue(queue_name, "inaktive")
            session.add(queue)
            session.commit()
            session.refresh(queue)

            return {
                "result": _views.RESULT_OK,
                **_schemas.WorkerQueue().dump(queue).data,
            }


@_view.view_defaults(route_name="specific_queue")
class WorkerQueue(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET", renderer="json")
    def get_one(self):
        worker_queue_id = self.request.matchdict.get("id")
        with _views.dbsession(self.request) as session:
            queue = session.query(
                _models.WorkerQueue
            ).get(worker_queue_id)
            if queue is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Worker with id {worker_queue_id} not found",
                    "data": None,
                }
            return {
                "result": _views.RESULT_OK,
                **_schemas.WorkerQueue().dump(queue).data,
            }

    @_view.view_config(request_method="PATCH", renderer="json")
    def update_one(self):
        worker_queue_id = self.request.matchdict.get("id")
        try:
            data = self.request.json
            _log.debug("Data: %s", data)
        except _json.decoder.JSONDecodeError as decode_error:
            return {
                "result": _views.RESULT_ERROR,
                "error": decode_error.msg,
                "data": None,
            }
        queue_name = data.get("name")
        with _views.dbsession(self.request) as session:
            queue = session.query(
                _models.WorkerQueue
            ).get(worker_queue_id)
            if queue is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Worker with id {worker_queue_id} not found",
                    "data": None,
                }
            queue.name = queue_name
            session.commit()
            return {
                "result": _views.RESULT_OK,
                **_schemas.WorkerQueue().dump(queue).data,
            }


def includeme(config):
    config.add_route("all_queues", "/workerqueues")
    config.add_route("specific_queue", "/workerqueues/:id")
