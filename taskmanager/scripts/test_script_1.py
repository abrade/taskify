#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys as _sys
import logging as _logging
import time as _time

import click as _click

import pyramid.paster as _paster

_log = _logging.getLogger(__name__)


@_click.command()
@_click.argument("config", required=True)
@_click.option("--timeout", envvar="TIMEOUT", type=int, default=0)
@_click.option(
    "--abort",
    envvar="ABORT",
    default=False,
    is_flag=True,
    type=bool,
)
def simulate_work(config, timeout, abort):
    _paster.setup_logging(config)
    # settings = _paster.get_appsettings(config)
    _log.info(
        "Starting Task simulate_work with options {}, {}".format(
            timeout,
            abort,
        )
    )
    _time.sleep(timeout)
    _log.info("awake .... ")
    if abort:
        raise RuntimeError("Wanna abort...")


def main(argv=tuple(_sys.argv)):
    simulate_work()
