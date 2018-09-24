# -*- coding: utf-8 -*-

import logging as _logging
import time as _time

import pyramid.paster as _paster

_log = _logging.getLogger(__name__)


def simulate_function(config, timeout, abort):
    _paster.setup_logging(config)
    timeout = int(timeout)
    if not isinstance(abort, bool):
        abort = abort == 'True'
    print('{}, {}, {}'.format(config, timeout, abort))
    _log.info(
        "Starting function simulate function with options {}, {}".format(
            timeout,
            abort,
        )
    )

    _time.sleep(timeout)
    print('awka...')
    if abort:
        raise RuntimeError("Wanna abort...")
