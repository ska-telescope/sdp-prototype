#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2019
#    Copyright by UWA (in the framework of the ICRAR)
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#


import json

import pkg_resources

from dlg.deploy import common
from dlg.dropmake import pg_generator
from dlg.manager import constants, client


def _get_lg(_workflow_id, _workflow_version):
    lg_fname = pkg_resources.resource_filename(
        __name__, 'logical_graphs/simple_graph.json')
    with open(lg_fname, 'rt') as f:
        return json.load(f)


def _create_pg(logical_graph, processing_block, node_managers,
               data_island_manager, zero_cost_run):

    logical_graph = pg_generator.fill(
        logical_graph, processing_block.parameters)

    unroll_kwargs = {}
    if zero_cost_run:
        unroll_kwargs['zerorun'] = True
        unroll_kwargs['app'] = 'dlg.apps.simple.SleepApp'
    physical_graph_template = pg_generator.unroll(
        logical_graph, **unroll_kwargs)
    physical_graph = pg_generator.partition(
        physical_graph_template,
        'mysarkar',
        num_partitions=len(node_managers),
        num_islands=1)
    physical_graph = pg_generator.resource_map(
        physical_graph,
        [data_island_manager] +
        node_managers,
        num_islands=1)
    return physical_graph


def run_processing_block(processing_block, status_callback, host='127.0.0.1',
                         port=constants.ISLAND_DEFAULT_REST_PORT, zero_cost_run=False):
    """Runs a ProcessingBlock to completion under daliuge"""

    session_id = 'pb_%s' % processing_block.pb_id
    logical_graph = _get_lg(
        processing_block.workflow['id'],
        processing_block.workflow['version'])

    status_callback('preparing')
    nodes = client.CompositeManagerClient(host, port, timeout=None).nodes()
    physical_graph = _create_pg(
        logical_graph, processing_block, nodes, host, zero_cost_run=zero_cost_run)
    common.submit(physical_graph, host=host, port=port, session_id=session_id)
    status_callback('running')
    common.monitor_sessions(session_id=session_id, host=host, port=port)
    status_callback('finished')
