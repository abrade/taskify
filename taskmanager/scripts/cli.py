#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click as _click

import taskmanager.commands as _commands


@_click.group()
def cli():
    pass


cli.add_command(_commands.worker)
cli.add_command(_commands.team)
cli.add_command(_commands.script)
cli.add_command(_commands.task)
cli.add_command(_commands.queue)

def main():
    cli()
