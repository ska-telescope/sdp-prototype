
Running the SDP Prototype stand-alone
=====================================

Deploying SDP
-------------

### Deploy the SDP components

At this point you should be able to deploy the SDP components. First go
to the charts directory:

```bash
    $ cd [sdp-prototype]/charts
```

Then for Helm 2, execute:

```bash
    $ helm install sdp-prototype -n sdp-prototype
```

or for Helm3, execute:

```bash
    $ helm install sdp-prototype sdp-prototype
```

You can again watch the fireworks using `kubectl`:

```bash
    $ kubectl get pod --watch
```

Pods associated with Tango might go down a couple times before they
start correctly, this seems to be normal. You can check the logs of
pods (copy the full name from `kubectl` output) to verify that they
are doing okay:

```bash
    $ kubectl logs sdp-prototype-tangods-[...] sdp-subarray-1
    2019-11-21 16:49:01,097 | INFO    | Initialising SDP Subarray: mid_sdp/elt/subarray_1
    ...
    2019-11-21 16:49:01,104 | INFO    | SDP Subarray initialised: mid_sdp/elt/subarray_1
    $ kubectl logs sdp-prototype-processing-controller-[...]
    ...
    DEBUG:main:Waiting...
    $ kubectl logs sdp-prototype-helm-deploy-[...]
    ...
    INFO:main:Found 0 existing deployments.
```

Just to name a few. If it's looking like this, there's a good chance
everything has been deployed correctly.

Deploying SDP on Windows
----------

### Starting up

```bash
    > minikube start
    > helm install etcd stable/etcd-operator
    > kubectl get pod --watch
```

In directory deploy/charts:

```bash
    > helm install sdp-prototype sdp-prototype
    > kubectl get pod --watch
```

#### Configuration Database

Find and set the host and port:

```bash
    > minikube service --url sdp-prototype-etcd-nodeport
    > set SDP_CONFIG_HOST=...
    > set SDP_CONFIG_PORT=...
```

This doesn't produce a (directly) runnable file on Windows:

```bash
    > pip install -U ska-sdp-config
```

But can do:

```bash
    > cd src\config_db\ska_sdp_config
```

Add to cli.py:

```bash
    if __name__ == "__main__":
        main(sys.argv[1:])
```

Then run

```bash
    > python cli.py ...
```

Testing it out
--------------

### Connecting to the configuration database

The deployment scripts should have exposed the SDP configuration
database (i.e. etcd) via a NodePort service. For Docker Desktop, this
should automatically expose the port on localhost, you just need to
find out which one:

```bash
    $ kubectl get service sdp-prototype-etcd-nodeport
    NAME                          TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
    sdp-prototype-etcd-nodeport   NodePort   10.97.188.221   <none>        2379:32234/TCP   3h56m
```

Set the environment variable `SDP_CONFIG_PORT` according to the
second part of the `PORTS(S)` column:

```bash
    $ export SDP_CONFIG_PORT=32234
```

For Minikube, you need to set both `SDP_CONFIG_HOST` and
`SDP_CONFIG_PORT`, but you can easily query both using
`minikube service`:

```bash
    $ minikube service --url sdp-prototype-etcd-nodeport
    http://192.168.39.45:32234
    $ export SDP_CONFIG_HOST=192.168.39.45
    $ export SDP_CONFIG_PORT=32234
```

This will allow you to connect with the `sdpcfg` utility:

```bash
    $ pip install -U ska-sdp-config
    $ sdpcfg ls -R /
    Keys with / prefix:
```

Which correctly shows that the configuration is currently empty.

### Start a workflow

Assuming the configuration is prepared as explained in the previous
section, we can now add a processing block to the configuration:

```bash
    $ sdpcfg process realtime:testdask:0.1.0
    OK, pb_id = realtime-20191121-0000
```

The processing block is created with the `/pb` prefix in the
configuration:

```bash
    $ sdpcfg ls values -R /pb
    Keys with /pb prefix:
    /pb/realtime-20191121-0000 = {
      "parameters": {},
      "pb_id": "realtime-20191121-0000",
      "sbi_id": null,
      "scan_parameters": {},
      "workflow": {
        "id": "testdask",
        "type": "realtime",
        "version": "0.1.0"
      }
    }
    /pb/realtime-20191121-0000/owner = {
      "command": [
        "testdask.py",
        "realtime-20191121-0000"
      ],
      "hostname": "realtime-20191121-0000-workflow-7bf947687f-9h9gz",
      "pid": 1
    }
```

The processing block is detected by the processing controller which
deploys the workflow. The workflow in turn deploys the execution engines
(in this case, Dask). The deployments are requested by creating entries
with `/deploy` prefix in the configuration, where they are detected by
the Helm deployer which actually makes the deployments:

```bash
    $ sdpcfg ls values -R /deploy
    Keys with /deploy prefix:
    /deploy/realtime-20191121-0000-dask = {
      "args": {
        "chart": "stable/dask",
        "values": {
          "jupyter.enabled": "false",
          "scheduler.serviceType": "ClusterIP",
          "worker.replicas": 2
        }
      },
      "deploy_id": "realtime-20191121-0000-dask",
      "type": "helm"
    }
    /deploy/realtime-20191121-0000-workflow = {
      "args": {
        "chart": "workflow",
        "values": {
          "env.SDP_CONFIG_HOST": "sdp-prototype-etcd-client.default.svc.cluster.local",
          "env.SDP_HELM_NAMESPACE": "sdp",
          "pb_id": "realtime-20191121-0000",
          "wf_image": "nexus.engageska-portugal.pt/sdp-prototype/workflow-testdask:0.1.0"
        }
      },
      "deploy_id": "realtime-20191121-0000-workflow",
      "type": "helm"
    }
```

The deployments associated with the processing block have been created
in the `sdp` namespace, so to view the created pods we have to ask as
follows:

```bash
    $ kubectl get pod -n sdp
    NAME                                                    READY   STATUS    RESTARTS   AGE
    realtime-20191121-0000-dask-scheduler-6c7cc64c7-jfczn   1/1     Running   0          113s
    realtime-20191121-0000-dask-worker-7cb8cdf6bd-mtc9w     1/1     Running   3          113s
    realtime-20191121-0000-dask-worker-7cb8cdf6bd-tdzkp     1/1     Running   3          113s
    realtime-20191121-0000-workflow-7bf947687f-9h9gz        1/1     Running   0          118s
```

### Cleaning up

Finally, let us remove the processing block from the configuration:

```bash
    $ sdpcfg delete /pb/realtime-[...]
```

If you re-run the commands from the last section you will notice that
this correctly causes all changes to the cluster configuration to be
undone as well.

Accessing Tango
---------------

By default the chart installs the iTango shell pod from the tango-base
chart. You can access it as follows:

```bash
    $ kubectl exec -it itango-tango-base-sdp-prototype /venv/bin/itango3
```

You should be able to query the SDP Tango devices:

```bash
    In [1]: lsdev
    Device                                   Alias                     Server                    Class
    ---------------------------------------- ------------------------- ------------------------- --------------------
    mid_sdp/elt/master                                                 SDPMaster/1               SDPMaster
    sys/tg_test/1                                                      TangoTest/test            TangoTest
    sys/database/2                                                     DataBaseds/2              DataBase
    sys/access_control/1                                               TangoAccessControl/1      TangoAccessControl
    mid_sdp/elt/subarray_1                                             SDPSubarray/1             SDPSubarray
```

This allows direction interaction with the devices, such as querying and
and changing attributes and issuing commands:

```bash
    In [2]: d = DeviceProxy('mid_sdp/elt/subarray_1')

    In [3]: d.obsState
    Out[3]: <obsState.IDLE: 0>
    
    In [4]: d.state()
    Out[4]: tango._tango.DevState.OFF
    
    In [5]: d.adminMode = 'ONLINE'
    In [6]: d.AssignResources('')
    In [7]: d.state()
    Out[7]: tango._tango.DevState.ON
    
    In [8]: d.obsState
    Out[8]: <obsState.IDLE: 0>
    
    In [9]: d.Configure('{ "configure": { "id": "xyz", "sbiId": "xyz", "workflow": { "type": "realtime", "version": "0.1.0", "id": "vis_receive" }, "parameters": {}, "scanParameters": { "1": {} } } }')
    In [10]: d.obsState
    Out[10]: <obsState.READY: 2>
    
    In [11]: d.StartScan()
    In [12]: d.obsState
    Out[12]: <obsState.SCANNING: 3>
    
    In [13]: d.EndScan()
    In [14]: d.obsState
    Out[14]: <obsState.READY: 2>
```

Troubleshooting
---------------

## etcd doesn't start (DNS problems)

Something that often happens on home set-ups is that `sdp-prototype-etcd`
doesn't start, which means that quite a bit of the
SDP system will not work. Try executing `kubectl logs` on the pod to
get a log. You might see something like this as the last three lines:

```bash
    ... I | pkg/netutil: resolving sdp-prototype-etcd-9s4hbbmmvw.k8s-sdp-prototype-etcd.default.svc:2380 to 10.1.0.21:2380
    ... I | pkg/netutil: resolving sdp-prototype-etcd-9s4hbbmmvw.k8s-sdp-prototype-etcd.default.svc:2380 to 92.242.132.24:2380
    ... C | etcdmain: failed to resolve http://sdp-prototype-etcd-9s4hbbmmvw.sdp-prototype-etcd.default.svc:2380 to match --initial-cluster=sdp-prototype-etcd-9s4hbbmmvw=http://sdp-prototype-etcd-9s4hbbmmvw.sdp-prototype-etcd.default.svc:2380 ("http://10.1.0.21:2380"(resolved from "http://sdp-prototype-etcd-9s4hbbmmvw.sdp-prototype-etcd.default.svc:2380") != "http://92.242.132.24:2380"(resolved from "http://sdp-prototype-etcd-9s4hbbmmvw.sdp-prototype-etcd.default.svc:2380"))
```

This informs you that `etcd` tried to resolve its own address, and for
some reason got two different answers both times. Interestingly, the 
`92.242.132.24` address is not actually in-cluster, but from the Internet,
and re-appears if we attempt to `ping` a nonexistent DNS name:

```bash
    $ ping does.not.exist
	Pinging does.not.exist [92.242.132.24] with 32 bytes of data:
    Reply from 92.242.132.24: bytes=32 time=25ms TTL=242
```

What is going on here is that that your ISP has installed a DNS server
that redirects unknown DNS names to a server showing a 'helpful' error
message complete with a bunch of advertisements. For some reason this
seems to cause a problem with Kubernetes' internal DNS resolution.

How can this be prevented? Theoretically it should be enough to force
the DNS server to one that doesn't have this problem (like Google's
`8.8.8.8` and `8.8.4.4` DNS servers), but that is tricky to get working.
Alternatively you can simply restart the entire thing until it works.
Unfortunately this is not quite as straightforward with `etcd-operator`,
as it sets the `restartPolicy` to `Never`, which means that any `etcd`
pod only gets once chance, and then will remain `Failed` forever. The
quickest way I have found is to delete the `EtcdCluster` object, then
`upgrade` the chart in order to re-install it:

```bash
    $ kubectl delete etcdcluster sdp-prototype-etcd
    $ helm upgrade sdp-prototype sdp-prototype
```

This can generally be repeated until by pure chance the two DNS resolutions
return the same result and `etcd` starts up.