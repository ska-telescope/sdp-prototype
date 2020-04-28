"""
Command line utility for accessing SKA SDP configuration.

Usage:
  sdpcfg [options] (get|watch) <path>
  sdpcfg [options] [watch] (ls|list) [values] [-R] <path>
  sdpcfg [options] delete [-R] <path>
  sdpcfg [options] (create|update) <path> <value>
  sdpcfg [options] edit <path>
  sdpcfg [options] process <workflow> [<parameters>]
  sdpcfg [options] deploy <type> <name> <parameters>
  sdpcfg --help

Options:
  -q, --quiet          Cut back on unnecessary output
  --prefix <prefix>    Path prefix for high-level API

Environment Variables:
  SDP_CONFIG_BACKEND   Database backend (default etcd3)
  SDP_CONFIG_HOST      Database host address (default 127.0.0.1)
  SDP_CONFIG_PORT      Database port (default 2379)
  SDP_CONFIG_PROTOCOL  Database access protocol (default http)
  SDP_CONFIG_CERT      Client certificate
  SDP_CONFIG_USERNAME  User name
  SDP_CONFIG_PASSWORD  User password
"""

# pylint: disable=assignment-from-no-return
# pylint: disable=too-many-branches

import os
import sys
import re
import tempfile
import json
import subprocess
import docopt
import yaml
from ska_sdp_config import config, entity


def cmd_get(txn, path, args):
    """Get raw value from database."""
    val = txn.raw.get(path)
    if args['--quiet']:
        print(val)
    else:
        print("{} = {}".format(path, val))


def cmd_list(txn, path, args):
    """List raw keys/values from database."""
    recurse = (8 if args['-R'] else 0)
    keys = txn.raw.list_keys(path, recurse=recurse)
    if args['--quiet']:
        if args['values']:
            values = [txn.raw.get(key) for key in keys]
            print(" ".join(values))
        else:
            print(" ".join(keys))
    else:
        print("Keys with {} prefix:".format(path))
        if args['values']:
            for key in keys:
                value = txn.raw.get(key)
                print("{} = {}".format(key, value))
        else:
            for key in keys:
                print(key)


def cmd_create(txn, path, value, _args):
    """Create raw key."""
    txn.raw.create(path, value)


def cmd_update(txn, path, value, _args):
    """Update raw key value."""
    txn.raw.update(path, value)


def cmd_edit(txn, path):
    """Edit the value of a raw key."""
    val = txn.raw.get(path)
    try:

        # Attempt translation to YAML
        val_dict = json.loads(val)
        val_in = yaml.dump(val_dict)
        have_yaml = True

    except json.JSONDecodeError:

        val_in = val
        have_yaml = False

    # Write to temporary file
    with tempfile.NamedTemporaryFile(
            'w', suffix=('.yml' if have_yaml else '.dat'),
            prefix=os.path.basename(path), delete=False) as tmp:
        print(val_in, file=tmp, flush=True)
        fname = tmp.name

    # Start editor
    subprocess.call([os.environ['EDITOR'] + " " + fname], shell=True)

    # Read new value in
    with open(fname) as tmp:
        new_val = tmp.read()
    if have_yaml:
        new_val = config.dict_to_json(yaml.safe_load(new_val))

    # Apply update
    if new_val == val:
        print("No change!")
    else:
        txn.raw.update(path, new_val)


def cmd_delete(txn, path, args):
    """Delete a key."""
    if args['-R']:
        for key in txn.raw.list_keys(path, recurse=8):
            if not args['--quiet']:
                print(key)
            txn.raw.delete(key)
    else:
        txn.raw.delete(path)


def cmd_create_pb(txn, workflow, parameters, _args):
    """Create a processing block."""
    # Parse parameters
    if parameters is not None:
        pars = yaml.safe_load(parameters)
    else:
        pars = {}

    # Create new processing block ID, create processing block
    pb_id = txn.new_processing_block_id('sdpcfg')
    txn.create_processing_block(entity.ProcessingBlock(
        pb_id, None, workflow, parameters=pars))
    return pb_id


def cmd_deploy(txn, typ, deploy_id, parameters):
    """Create a deployment."""
    dct = yaml.safe_load(parameters)
    txn.create_deployment(entity.Deployment(deploy_id, typ, dct))


def main(argv):
    """Command line interface implementation."""
    args = docopt.docopt(__doc__, argv=argv)

    # Validate
    path = args["<path>"]
    success = True
    if path is not None:
        if path[0] != '/':
            print("Path must start with '/'!", file=sys.stderr)
            success = False
        if args['list'] is None and path[-1] == '/':
            print("Key path must not end with '/'!", file=sys.stderr)
            success = False
        if not re.match('^[a-zA-Z0-9_\\-/]*$', path):
            print("Path contains non-permissible characters!", file=sys.stderr)
            success = False
    workflow = args['<workflow>']
    if workflow is not None:
        workflow = workflow.split(':')
        if len(workflow) != 3:
            print("Please specify workflow as 'type:name:version'!",
                  file=sys.stderr)
            success = False
        else:
            workflow = {
                'type': workflow[0],
                'id': workflow[1],
                'version': workflow[2]
            }

    # Input can be taken from stdin
    value = args["<value>"]
    if value == '-':
        value = sys.stdin.read()
    parameters = args["<parameters>"]
    if parameters == '-':
        parameters = sys.stdin.read()
    if not success:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    cmd(args, path, value, workflow, parameters)


def cmd(args, path, value, workflow, parameters):
    """Execute command."""
    # Get configuration client, start transaction
    prefix = ('' if args['--prefix'] is None else args['--prefix'])
    cfg = config.Config(global_prefix=prefix)
    try:
        for txn in cfg.txn():
            if args['ls'] or args['list']:
                cmd_list(txn, path, args)
            elif args['watch'] or args['get']:
                cmd_get(txn, path, args)
            elif args['create']:
                cmd_create(txn, path, value, args)
            elif args['edit']:
                cmd_edit(txn, path)
            elif args['update']:
                cmd_update(txn, path, value, args)
            elif args['delete']:
                cmd_delete(txn, path, args)
            elif args['process']:
                pb_id = cmd_create_pb(txn, workflow, parameters, args)
            elif args['deploy']:
                cmd_deploy(txn, args['<type>'], args['<name>'], parameters)
            if args['watch']:
                txn.loop(wait=True)

        # Possibly give feedback after transaction has concluded
        if not args['--quiet']:
            if args['create'] or args['update'] or args['delete'] or \
               args['edit']:
                print("OK")
            if args['process']:
                print("OK, pb_id = {}".format(pb_id))

    except KeyboardInterrupt:
        if not args['watch']:
            raise
