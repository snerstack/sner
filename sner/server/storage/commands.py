# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
storage commands
"""

import json
import os
import sys

import click
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy import func, or_
from sqlalchemy_filters import apply_filters

from sner.lib import format_host_address
from sner.server.extensions import db
from sner.server.parser import registered_parsers
from sner.server.sqlafilter import filter_parser
from sner.server.storage.core import vuln_report
from sner.server.storage.models import Host, Note, Service, Vuln


@click.group(name='storage', help='sner.server storage management')
def command():
    """storage commands container"""


@command.command(name='import', help='import data from files')
@with_appcontext
@click.argument('parser')
@click.argument('path', nargs=-1)
def storage_import(path, parser):
    """import data"""

    if parser not in registered_parsers:
        current_app.logger.error('no such parser')
        sys.exit(1)

    parser_impl = registered_parsers[parser]
    for item in path:
        if os.path.isfile(item):
            parser_impl.import_file(item)
    sys.exit(0)


@command.command(name='flush', help='flush all objects from storage')
@with_appcontext
def storage_flush():
    """flush all objects from storage"""

    db.session.query(Host).delete()
    db.session.commit()


@command.command(name='report', help='generate vuln report')
@with_appcontext
def storage_report():
    """generate vuln report"""
    print(vuln_report())


@command.command(name='host-cleanup', help='cleanup hosts; remove hosts not associated with any data (eg. just addresses)')
@with_appcontext
@click.option('--dry', is_flag=True, help='do not actually remove')
def storage_host_cleanup(**kwargs):
    """
    clean up storage, will remove all hosts:
        * without any data attribute set
        * having no service, vuln or note
    """

    services_count = func.count(Service.id)
    vulns_count = func.count(Vuln.id)
    notes_count = func.count(Note.id)
    query_hosts = Host.query \
        .outerjoin(Service, Host.id == Service.host_id).outerjoin(Vuln, Host.id == Vuln.host_id).outerjoin(Note, Host.id == Note.host_id) \
        .filter(
            or_(Host.os == '', Host.os == None),  # noqa: E711  pylint: disable=singleton-comparison
            or_(Host.comment == '', Host.comment == None)  # noqa: E711  pylint: disable=singleton-comparison
        ) \
        .having(services_count == 0).having(vulns_count == 0).having(notes_count == 0).group_by(Host.id)

    if kwargs['dry']:
        for host in query_hosts.all():
            print(host)

        # do not commit, it's dry test
        db.session.rollback()
    else:
        for host in query_hosts.all():
            db.session.delete(host)
        db.session.commit()


@command.command(name='service-list', help='service (filtered) listing')
@with_appcontext
@click.option('--filter', help='filter query')
@click.option('--hostnames', is_flag=True, help='show host.hostname')
@click.option('--short', is_flag=True, help='show only service.host.address/hostname')
@click.option('--long', is_flag=True, help='show service extended info')
def storage_service_list(**kwargs):
    """service listing; used to feed manymap queues from storage data"""

    def get_host(svc, hostnames=False):
        """return address or hostname"""

        if hostnames and svc.host.hostname:
            return svc.host.hostname
        return format_host_address(svc.host.address)

    def get_data(svc):
        """return common data as dict"""
        return {'proto': svc.proto, 'port': svc.port, 'name': svc.name, 'state': svc.state, 'info': json.dumps(svc.info)}

    if kwargs['long'] and kwargs['short']:
        current_app.logger.error('--short and --long are mutualy exclusive options')
        sys.exit(1)

    query = Service.query
    if kwargs['filter']:
        query = apply_filters(query, filter_parser.parse(kwargs['filter']), do_auto_join=False)

    fmt = '{proto}://{host}:{port}'
    if kwargs['short']:
        fmt = '{host}'
    elif kwargs['long']:
        fmt = '{proto}://{host}:{port} {name} {state} {info}'

    for tmp in query.all():
        print(fmt.format(**get_data(tmp), host=get_host(tmp, kwargs['hostnames'])))


@command.command(name='service-cleanup', help='cleanup services; remove all in "filtered" state')
@with_appcontext
@click.option('--dry', is_flag=True, help='do not actually remove')
def storage_service_cleanup(**kwargs):
    """clean up storage, will remove all services in any of 'filtered' state"""

    query_services = Service.query.filter(Service.state.ilike('filtered%'))
    if kwargs['dry']:
        for service in query_services.all():
            print(service)

        # do not commit, it's dry test
        db.session.rollback()
    else:
        for service in query_services.all():
            db.session.delete(service)
        db.session.commit()
