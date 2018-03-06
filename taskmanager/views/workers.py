# -*- coding: utf-8 -*-

import logging as _logging
import json as _json

import pyramid.view as _view

import taskmanager.views as _views
import taskmanager.models as _models
import taskmanager.models.schemas as _schemas

_log = _logging.getLogger(__name__)


@_view.view_defaults(route_name="all_workers", renderer="json")
class Workers(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET")
    def get(self):
        with _views.dbsession(self.request) as session:
            workers = session.query(
                _models.Worker
            ).all()
            return {
                "result": _views.RESULT_OK,
                **_schemas.Worker(many=True).dump(workers).data,
            }

    @_view.view_config(request_method="POST")
    def post(self):
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
        worker_name = data.get("name")
        if worker_name is None:
            return {
                "result": _views.RESULT_ERROR,
                "error": "No name is given",
                "data": None,
            }
        with _views.dbsession(self.request) as session:
            worker = _models.Worker(worker_name, "OFFLINE")
            session.add(worker)
            session.commit()
            session.refresh(worker)

            return {
                "result": _views.RESULT_OK,
                **_schemas.Worker().dump(worker).data,
            }


@_view.view_defaults(route_name="specific_worker", renderer="json")
class Worker(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET")
    def get_one(self):
        worker_id = self.request.matchdict.get("id")
        with _views.dbsession(self.request) as session:
            worker = session.query(
                _models.Worker
            ).get(worker_id)
            if worker is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Worker with id {worker_id} not found",
                    "data": None,
                }
            return {
                "result": _views.RESULT_OK,
                **_schemas.Worker().dump(worker).data,
            }

    @_view.view_config(request_method="PATCH")
    def update_one(self):
        worker_id = self.request.matchdict.get("id")
        try:
            data = self.request.json
            _log.debug("Data: %s", data)
        except _json.decoder.JSONDecodeError as decode_error:
            return {
                "result": _views.RESULT_ERROR,
                "error": decode_error.msg,
                "data": None,
            }
        worker_name = data.get("name")
        with _views.dbsession(self.request) as session:
            worker = session.query(
                _models.Worker
            ).get(worker_id)
            if worker is None:
                return {
                    "result": _views.RESULT_NOTFOUND,
                    "error": f"Worker with id {worker_id} not found",
                    "data": None,
                }
            worker.name = worker_name
            session.commit()
            return {
                "result": _views.RESULT_OK,
                **_schemas.Worker().dump(worker).data,
            }


@_view.view_defaults(route_name="worker_opt", renderer="json")
class WorkerOption(object):
    def __init__(self, request):
        self.request = request

    @_view.view_config(request_method="GET")
    def get_option(self):
        worker_id = self.request.params.get("worker_id")
        with _views.dbsession(self.request) as session:
            if worker_id:
                worker = session.query(
                    _models.Worker
                ).get(worker_id)
                i = _views.celery_app.control.inspect([worker.name])
                stats = i.stats()
                options = {
                    "id": worker_id
                }
                if stats and worker.name in stats:
                    stats = stats[worker.name]
                    options.update(
                        {
                            "id": worker_id,
                            "concurrency": stats["pool"]["max-concurrency"],
                            "prefetchcount": stats["prefetch_count"],
                            "statistics": stats["rusage"],
                        }
                    )
            return {
                "result": _views.RESULT_OK,
                **_schemas.WorkerOptions().dump(options).data,
            }


def includeme(config):
    config.add_route("all_workers", "/workers")
    config.add_route("specific_worker", "/workers/:id")
    config.add_route("worker_opt", "/workeroptions")
