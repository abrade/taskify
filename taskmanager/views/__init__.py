# -*- coding: utf-8 -*-

import os as _os
import math as _math
import configparser as _cp
import contextlib as _ct
import transaction as _ta
import subprocess as _subprocess
import importlib as _importlib

import celery as _celery
import celery.result as _result
import celery.exceptions as _exceptions

import psycopg2 as _psycopg2

import sqlalchemy.orm as _orm
import celery.utils.log as _logging

import taskmanager.models as _models

_log = _logging.get_task_logger(__name__)

RESULT_OK = "OK"
RESULT_ERROR = "ERROR"
RESULT_NOTFOUND = "NOT_FOUND"

celery_app = None

if celery_app is None:
    cfg_parser = _cp.ConfigParser()
    cfg_parser.read(
        [
            _os.path.expanduser('~/.taskmanager.conf'),
            '/etc/taskmanager.conf'
        ]
    )
    celery_config = cfg_parser['celery']
    celery_app = _celery.Celery(**dict(celery_config))
    celery_app.conf.task_default_queue = 'default'
    celery_app.conf.task_queues = []


def get_result(task_id):
    res = _result.AsyncResult(task_id, app=celery_app, timeout=300)
    try:
        return res.get()
    except _exceptions.TimeoutError:
        return {}


@celery_app.task(retry_kwargs={'max_retries': 5})
def start_task(executable, config, options, additional_info=None):
    current_env = _os.environ.copy()
    for k, v in options.items():
        if isinstance(v, int):
            options[k] = str(v)
    current_env.update(options)
    current_env["TASK_ID"] = start_task.request.id
    current_env["PARENT_ID"] = ''
    if additional_info and "parent_id" in additional_info:
        current_env["PARENT_ID"] = str(additional_info.get("parent_id", ""))
    cmd = [executable, config]
    try:
        task = _subprocess.Popen(
            cmd,
            env=current_env,
            shell=True,
            stdout=_subprocess.PIPE,
            stderr=_subprocess.PIPE,
        )
        stdout, stderr = task.communicate()
        if task.returncode != 0:
            _log.info("retry...")
            start_task.retry()
        else:
            return (
                task.returncode,
                stdout.decode('utf-8'),
                stderr.decode('utf-8'),
            )
    except Exception as e:
        _log.error("Something happen .... retry... %r", e)
        start_task.retry()


@celery_app.task(retry_kwargs={'max_retries': 5})
def start_function(function, config, args, additional_info=None):
    print('{}, {}, {}'.format(function, args, additional_info))
    module, func = function.rsplit('.', 1)
    try:
        module = _importlib.import_module(module)
    except ImportError as e:
        return (-1, '', e)

    func = getattr(module, func)
    if func is None:
        return (-1, '', 'Function not found!')
    try:
        if isinstance(args, (list, tuple)):
            ret = func(config, *args)
        elif isinstance(args, dict):
            ret = func(config, **args)
    except Exception as e:
        print('EXCEPTION : %r', e)
        _log.error("Catched exception ... %r", e)
        start_function.retry()

    return (0, ret, '')


@_ct.contextmanager
def dbsession(request):
    settings = request.registry.settings
    engine = _models.get_engine(settings)
    session_factory = _models.get_session_factory(engine)
    db_session = _orm.scoped_session(session_factory)
    yield db_session
    db_session.remove()
    engine.dispose()
    # with _ta.manager:
    #     yield _models.get_tm_session(session_factory, _ta.manager)


@_ct.contextmanager
def get_connection(request):
    settings = request.registry.settings
    yield _psycopg2.connect(settings['sqlalchemy.url'])


def create_links(base_url, page, max_entries, max_elements):
    count = _math.ceil(max_elements / max_entries)
    next_page = page + 1 if (page + 1) < count else count
    prev_page = page - 1 if page - 1 >= 0 else 0
    base_unformat_url = "{}?page[number]={}&page[size]={}"
    return {
        "self": base_unformat_url.format(base_url, page, max_elements),
        "next": base_unformat_url.format(base_url, next_page, max_entries),
        "prev": base_unformat_url.format(base_url, prev_page, max_entries),
        "first": base_unformat_url.format(base_url, 0, max_entries),
        "last": base_unformat_url.format(base_url, count - 1, max_entries),
    }
