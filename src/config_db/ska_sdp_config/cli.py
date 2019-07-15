"""
Usage:
  sdpcfg [options] (get|watch) <path>
  sdpcfg [options] [watch] list [values] <path>
  sdpcfg [options] delete <path>
  sdpcfg [options] (create|update) <path> <value>
  sdpcfg [options] create_pb <workflow>
  sdpcfg --help

Options:
  -q, --quiet          Cut back on unneccesary output

Environment Variables:
  SDP_CONFIG_BACKEND   Database backend (default etcd3)
  SDP_CONFIG_HOST      Database host address (default 127.0.0.1)
  SDP_CONFIG_PORT      Database port (default 2379)
  SDP_CONFIG_PROTOCOL  Database access protocol (default http)
  SDP_CONFIG_CERT      Client certificate
  SDP_CONFIG_USERNAME  User name
  SDP_CONFIG_PASSWORD  User password
"""

import docopt
import sys
import re
from ska_sdp_config import entity

def cmd_get(txn, path, args):
    val = txn._txn.get(path)
    if args['--quiet']:
        print(val)
    else:
        print("{} = {}".format(path, val))

def cmd_list(txn, path, args):
    keys = txn._txn.list_keys(path)
    if args['--quiet']:
        if args['values']:
            values = [ txn._txn.get(key) for key in keys ]
            print(", ".join(values))
        else:
            print(", ".join(keys))
    else:
        if args['values']:
            print("Keys with {} prefix:".format(path))
            for key in keys:
                value = txn._txn.get(key)
                print("{} = {}".format(key, value))
        else:
            print("Keys with {} prefix: {}".format(path, ", ".join(keys)))

def cmd_create(txn, path, value, args):
    txn._txn.create(path, value)

def cmd_update(txn, path, value, args):
    txn._txn.update(path, value)

def cmd_delete(txn, path, args):
    txn._txn.delete(path)

def cmd_create_pb(txn, workflow, args):
    pb_id = txn.new_processing_block_id(workflow['type'])
    txn.create_processing_block(entity.ProcessingBlock(pb_id, None, workflow))
    return pb_id

def main():
    args = docopt.docopt(__doc__)

    # Validate
    path = args["<path>"]
    success = True
    if path is not None:
        if path[0] != '/':
            print("Path must start with '/'!", file=sys.stderr)
            success=False
        if args['list'] is None and path[-1] == '/':
            print("Key path must not end with '/'!", file=sys.stderr)
            success=False
        if not re.match('^[a-zA-Z0-9_\-/]*$', path):
            print("Path contains non-permissable characters!", file=sys.stderr)
            success=False
    workflow = args['<workflow>']
    if workflow is not None:
        workflow = workflow.split(':')
        if len(workflow) != 3:
            print("Please specify workflow as 'type:name:version'!", file=sys.stderr)
            success = False
        else:
            workflow = {
                'type': workflow[0],
                'name': workflow[1],
                'version': workflow[2]
            }

    # Input can be taken from stdin
    value = args["<value>"]
    if value == '-':
        value = sys.stdin.read()
    if not success:
        print(__doc__, file=sys.stderr)
        exit(1)

    # Get configuration client, start transaction
    import ska_sdp_config
    cfg = ska_sdp_config.Config()
    try:
        for txn in cfg.txn():
            if args['list']:
                cmd_list(txn, path, args)
            elif args['watch'] or args['get']:
                cmd_get(txn, path, args)
            elif args['create']:
                cmd_create(txn, path, value, args)
            elif args['update']:
                cmd_update(txn, path, value, args)
            elif args['delete']:
                cmd_delete(txn, path, args)
            elif args['create_pb']:
                pb_id = cmd_create_pb(txn, workflow, args)
            if args['watch']:
                txn.loop(wait=True)

        # Possibly give feedback after transaction has concluded
        if not args['--quiet']:
            if args['create'] or args['update'] or args['delete']:
                print("OK")
            if args['create_pb']:
                print("OK, pb_id = {}".format(pb_id))

    except KeyboardInterrupt as e:
        if not args['watch']:
            raise
