# -*- coding: utf-8 -*-

import logging as _logging

import taskmanager.views as _views
import taskmanager.models as _models
import taskmanager.models.schemas as _schemas

_log = _logging.getLogger(__name__)


class Workers(_views.BaseResource):
    NAME = "workers"

    @_views.get_all()
    @_views.with_model(output_model=_schemas.Worker)
    @_views.with_links
    def get(self, include_data=None, page=0, size=20):
        with _views.dbsession(self.request) as session:
            workers = session.query(
                _models.Worker
            )
            max_elements = workers.count()
            workers = workers.offset(
                page*size
            ).limit(
                size
            ).all()
            return {
                'meta': {
                    'page': page,
                    'max_entries': size,
                    'max_elements': max_elements,
                },
                'data': workers,
            }

    @_views.post_one()
    @_views.with_model(model=_schemas.Worker)
    def post(self, post_data):
        worker_name = post_data.get("name")
        if worker_name is None:
            raise _views.RestAPIException(
                "No name is given",
                _views.RESULT_ERROR,
            )
        with _views.dbsession(self.request) as session:
            worker = _models.Worker(worker_name, "OFFLINE")
            session.add(worker)
            session.commit()
            session.refresh(worker)

            return worker

    @_views.get_one(param="worker_id")
    @_views.with_model(output_model=_schemas.Worker)
    def get_one(self, worker_id):
        with _views.dbsession(self.request) as session:
            worker = session.query(
                _models.Worker
            ).get(worker_id)
            if worker is None:
                raise _views.RestAPIException(
                    f"Worker with id {worker_id} not found",
                    _views.RESULT_NOTFOUND,
                )
            return worker

    @_views.patch_one(param="worker_id")
    @_views.with_model(model=_schemas.Worker)
    def update_one(self, worker_id, post_data):
        worker_name = post_data.get("name")
        with _views.dbsession(self.request) as session:
            worker = session.query(
                _models.Worker
            ).get(worker_id)
            if worker is None:
                raise _views.RestAPIException(
                    f"Worker with id {worker_id} not found",
                    _views.RESULT_NOTFOUND,
                )
            worker.name = worker_name
            session.commit()
            session.refresh(worker)
            return worker


class WorkerOption(_views.BaseResource):
    NAME = "workeroptions"

    @_views.get_one(param="worker_id")
    def get_option(self, worker_id):
        with _views.dbsession(self.request) as session:
            if not worker_id:
                raise _views.RestAPIException(
                    f"Missing worker id",
                    _views.RESULT_ERROR,
                )
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
            return options


def includeme(config):
    Workers.init_handler(config)
    WorkerOption.init_handler(config)
