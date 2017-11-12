# -*- coding: utf-8 -*-

import os as _os
import configparser as _cp
import contextlib as _ct
import transaction as _ta
import subprocess as _subprocess

import celery as _celery
import kombu as _kombu


import sqlalchemy.orm as _orm
import celery.utils.log as _logging

import taskmanager.models as _models

_log = _logging.get_task_logger(__name__)

celery_app = None

if celery_app is None:
    cfg_parser = _cp.ConfigParser()
    cfg_parser.read([_os.path.expanduser('~/.taskmanager.conf'), '/etc/taskmanager.conf'])
    celery_config = cfg_parser['celery']
    celery_app = _celery.Celery(**dict(celery_config))
    celery_app.conf.task_default_queue = 'default'
    celery_app.conf.task_queues = []


@celery_app.task(retry_kwargs={'max_retries': 5})
def start_task(executable, options):
    current_env = _os.environ.copy()
    for k,v in options.items():
        if isinstance(v, int):
            options[k] = str(v)
    current_env.update(options)
    current_env["TASK_ID"] = start_task.request.id
    current_env["PARENT_ID"] = start_task.request.parent_id or ''
    print(start_task.request.__dict__)
    print(current_env)
    cmd = executable
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
            return (task.returncode, stdout.decode('utf-8'), stderr.decode('utf-8'))
    except Exception as e:
        _log.error("Something happen .... retry... %r", e)
        start_task.retry()

@_ct.contextmanager
def dbsession(request):
    settings = request.registry.settings
    engine = _models.get_engine(settings)
    session_factory = _models.get_session_factory(engine)
    yield _orm.scoped_session(session_factory)
    # with _ta.manager:
    #     yield _models.get_tm_session(session_factory, _ta.manager)

RESULT_OK = "OK"
RESULT_ERROR = "ERROR"
RESULT_NOTFOUND = "NOT_FOUND"
