
Running the SDP Prototype stand-alone
=====================================

Installing the etcd operator
----------------------------

The SDP configuration database is implemented on top of [etcd](https://etcd.io),
a strongly consistent, distributed key-value store that provides a reliable way
to store data that needs to be accessed by a distributed system or cluster of
machines.

Before deploying the SDP itself, you need to install the `etcd-operator` Helm
chart. This provides a convenient way to create and manage etcd clusters in
other charts.

If you have a fresh install of Helm, you need to add the `stable` repository:

```console
$ helm repo add stable https://kubernetes-charts.storage.googleapis.com/
```

The `sdp-prototype` charts directory contains a file called
`etcd-operator.yaml` with settings for the chart. This turns off parts which
are not used (the backup and restore operators).

First go to the charts directory:

```console
$ cd [sdp-prototype]/charts
```

Then install the `etcd-operator` chart with:

```console
$ helm install etcd stable/etcd-operator -f etcd-operator.yaml
```

If you now execute:

```console
$ kubectl get pod --watch
```

You should eventually see an pod called `etcd-etcd-operator-etcd-operator-[...]`
in 'Running' state (yes, Helm is exceedingly redundant with its names). If not
wait a bit, if you try to go to the next step before this has completed there is
a  chance it will fail.

Deploying the SDP
-----------------

At this point you should be able to deploy the SDP. Install the `sdp-prototype`
chart with the release name `test`:

```console
$ helm install test sdp-prototype
```

You can again watch the deployment in progress using `kubectl`:

```console
$ kubectl get pod --watch
```

Pods associated with Tango might go down a couple times before they
start correctly, this seems to be normal. You can check the logs of
pods (copy the full name from `kubectl` output) to verify that they
are doing okay:

```console
$ kubectl logs test-sdp-prototype-lmc-[...] sdp-subarray-1
1|2020-08-06T15:17:41.369Z|INFO|MainThread|init_device|subarray.py#110|SDPSubarray|Initialising SDP Subarray: mid_sdp/elt/subarray_1
...
1|2020-08-06T15:17:41.377Z|INFO|MainThread|init_device|subarray.py#140|SDPSubarray|SDP Subarray initialised: mid_sdp/elt/subarray_1
$ kubectl logs test-sdp-prototype-processing-controller-[...]
...
1|2020-08-06T15:14:30.068Z|DEBUG|MainThread|main|processing_controller.py#192||Waiting...
$ kubectl logs test-sdp-prototype-helm-deploy-[...]
...
1|2020-08-06T15:14:31.662Z|INFO|MainThread|main|helm_deploy.py#146||Found 0 existing deployments.
```

If it looks like this, there is a good chance everything has been deployed
correctly.

Testing it out
--------------

### Connecting to the configuration database

By default the `sdp-prototype` chart deploys a 'console' pod which enables you
to interact with the configuration database. You can start a shell in the pod
by doing:

```console
$ kubectl exec -it deploy/test-sdp-prototype-console -- /bin/bash
```

This will allow you to use the `sdpcfg` command:

```console
# sdpcfg ls -R /
Keys with / prefix:
```

Which correctly shows that the configuration is currently empty.

### Starting a workflow

Assuming the configuration is prepared as explained in the previous
section, we can now add a processing block to the configuration:

```console
# sdpcfg process batch:test_dask:0.2.1
OK, pb_id = pb-sdpcfg-20200425-00000
```

The processing block is created with the `/pb` prefix in the
configuration:

```console
# sdpcfg ls values -R /pb
Keys with /pb prefix:
/pb/pb-sdpcfg-20200425-00000 = {
  "dependencies": [],
  "id": "pb-sdpcfg-20200425-00000",
  "parameters": {},
  "sbi_id": null,
  "workflow": {
    "id": "test_dask",
    "type": "batch",
    "version": "0.2.0"
  }
}
/pb/pb-sdpcfg-20200425-00000/owner = {
  "command": [
    "testdask.py",
    "pb-sdpcfg-20200425-00000"
  ],
  "hostname": "proc-pb-sdpcfg-20200425-00000-workflow-7pfkl",
  "pid": 1
}
/pb/pb-sdpcfg-20200425-00000/state = {
  "resources_available": true,
  "status": "RUNNING"
}
```

The processing block is detected by the processing controller which
deploys the workflow. The workflow in turn deploys the execution engines
(in this case, Dask). The deployments are requested by creating entries
with `/deploy` prefix in the configuration, where they are detected by
the Helm deployer which actually makes the deployments:

```console
# sdpcfg ls values -R /deploy
Keys with /deploy prefix:
/deploy/proc-pb-sdpcfg-20200425-00000-dask = {
  "args": {
    "chart": "stable/dask",
    "values": {
      "jupyter.enabled": "false",
      "scheduler.serviceType": "ClusterIP",
      "worker.replicas": 2
    }
  },
  "id": "proc-pb-sdpcfg-20200425-00000-dask",
  "type": "helm"
}
/deploy/proc-pb-sdpcfg-20200425-00000-workflow = {
  "args": {
    "chart": "workflow",
    "values": {
      "env.SDP_CONFIG_HOST": "test-sdp-prototype-etcd-client.default.svc.cluster.local",
      "env.SDP_HELM_NAMESPACE": "sdp",
      "pb_id": "pb-sdpcfg-20200425-00000",
      "wf_image": "nexus.engageska-portugal.pt/sdp-prototype/workflow-test-dask:0.2.0"
    }
  },
  "id": "proc-pb-sdpcfg-20200425-00000-workflow",
  "type": "helm"
}
```

The deployments associated with the processing block have been created
in the `sdp` namespace, so to view the created pods we have to ask as
follows (on the host):

```console
$ kubectl get pod -n sdp
NAME                                                            READY   STATUS    RESTARTS   AGE
proc-pb-sdpcfg-20200425-00000-dask-scheduler-78b4974ddf-w4x8x   1/1     Running   0          4m41s
proc-pb-sdpcfg-20200425-00000-dask-worker-85584b4598-p6qpw      1/1     Running   0          4m41s
proc-pb-sdpcfg-20200425-00000-dask-worker-85584b4598-x2bh5      1/1     Running   0          4m41s
proc-pb-sdpcfg-20200425-00000-workflow-7pfkl                    1/1     Running   0          4m46s
```

### Cleaning up

Finally, let us remove the processing block from the configuration (in the SDP
console shell):

```console
# sdpcfg delete -R /pb/pb-sdpcfg-20200425-00000
/pb/pb-sdpcfg-20200425-00000
/pb/pb-sdpcfg-20200425-00000/owner
/pb/pb-sdpcfg-20200425-00000/state
OK
```

If you re-run the commands from the last section you will notice that
this correctly causes all changes to the cluster configuration to be
undone as well.

Accessing Tango
---------------

By default the sdp-prototype chart installs the iTango shell pod from the
tango-base chart. You can access it as follows:

```console
$ kubectl exec -it itango-tango-base-sdp-prototype -- /venv/bin/itango3
```

You should be able to query the SDP Tango devices:

```python
In [1]: lsdev
Device                                   Alias                     Server                    Class
---------------------------------------- ------------------------- ------------------------- --------------------
mid_sdp/elt/master                                                 SdpMaster/1               SdpMaster
mid_sdp/elt/subarray_1                                             SdpSubarray/1             SdpSubarray
mid_sdp/elt/subarray_2                                             SdpSubarray/2             SdpSubarray
sys/access_control/1                                               TangoAccessControl/1      TangoAccessControl
sys/database/2                                                     DataBaseds/2              DataBase
sys/rest/0                                                         TangoRestServer/rest      TangoRestServer
sys/tg_test/1                                                      TangoTest/test            TangoTest
```

This allows direct interaction with the devices, such as querying and
and changing attributes and issuing commands:

```python
In [2]: d = DeviceProxy('mid_sdp/elt/subarray_1')

In [3]: d.state()
Out[3]: tango._tango.DevState.OFF

In [4]: d.On()

In [5]: d.state()
Out[5]: tango._tango.DevState.ON

In [6]: d.obsState
Out[6]: <obsState.EMPTY: 0>

In [7]: config_sbi = '''
    ...: {
    ...:   "id": "sbi-mvp01-20200425-00000",
    ...:   "max_length": 21600.0,
    ...:   "scan_types": [
    ...:     {
    ...:       "id": "science",
    ...:       "channels": [
    ...:         {"count": 372, "start": 0, "stride": 2, "freq_min": 0.35e9, "freq_max": 0.358e9, "link_map": [[0,0], [200,1]]}
    ...:       ]
    ...:     }
    ...:   ],
    ...:   "processing_blocks": [
    ...:     {
    ...:       "id": "pb-mvp01-20200425-00000",
    ...:       "workflow": {"type": "realtime", "id": "test_realtime", "version": "0.1.0"},
    ...:       "parameters": {}
    ...:     },
    ...:     {
    ...:       "id": "pb-mvp01-20200425-00001",
    ...:       "workflow": {"type": "realtime", "id": "test_realtime", "version": "0.1.0"},
    ...:       "parameters": {}
    ...:     },
    ...:     {
    ...:       "id": "pb-mvp01-20200425-00002",
    ...:       "workflow": {"type": "batch", "id": "test_batch", "version": "0.1.0"},
    ...:       "parameters": {},
    ...:       "dependencies": [
    ...:         {"pb_id": "pb-mvp01-20200425-00000", "type": ["visibilities"]}
    ...:       ]
    ...:     },
    ...:     {
    ...:       "id": "pb-mvp01-20200425-00003",
    ...:       "workflow": {"type": "batch", "id": "test_batch", "version": "0.1.0"},
    ...:       "parameters": {},
    ...:       "dependencies": [
    ...:         {"pb_id": "pb-mvp01-20200425-00002", "type": ["calibration"]}
    ...:       ]
    ...:     }
    ...:   ]
    ...: }
    ...: '''

In [8]: d.AssignResources(config_sbi)

In [9]: d.obsState
Out[9]: <obsState.IDLE: 0>

In [10]: d.Configure('{"scan_type": "science"}')

In [11]: d.obsState
Out[11]: <obsState.READY: 2>

In [12]: d.Scan('{"id": 1}')

In [13]: d.obsState
Out[13]: <obsState.SCANNING: 3>

In [14]: d.EndScan()

In [15]: d.obsState
Out[15]: <obsState.READY: 2>

In [16]: d.End()

In [17]: d.obsState
Out[17]: <obsState.IDLE: 0>

In [18]: d.ReleaseResources()

In [19]: d.obsState
Out[19]: <obsState.EMPTY: 0>

In [20]: d.Off()

In [21]: d.state()
Out[21]: tango._tango.DevState.OFF
```

Removing the SDP
----------------

To remove the SDP deployment from the cluster, do:

```console
$ helm uninstall test
```

and to remove the etcd operator, do:

```console
$ helm uninstall etcd
```

Troubleshooting
---------------

### etcd doesn't start (DNS problems)

Something that often happens on home set-ups is that `test-sdp-prototype-etcd`
does not start, which means that quite a bit of the SDP system will not work.
Try executing `kubectl logs` on the pod to get a log. You might see something
like this as the last three lines:

```console
... I | pkg/netutil: resolving sdp-prototype-etcd-9s4hbbmmvw.k8s-sdp-prototype-etcd.default.svc:2380 to 10.1.0.21:2380
... I | pkg/netutil: resolving sdp-prototype-etcd-9s4hbbmmvw.k8s-sdp-prototype-etcd.default.svc:2380 to 92.242.132.24:2380
... C | etcdmain: failed to resolve http://sdp-prototype-etcd-9s4hbbmmvw.sdp-prototype-etcd.default.svc:2380 to match --initial-cluster=sdp-prototype-etcd-9s4hbbmmvw=http://sdp-prototype-etcd-9s4hbbmmvw.sdp-prototype-etcd.default.svc:2380 ("http://10.1.0.21:2380"(resolved from "http://sdp-prototype-etcd-9s4hbbmmvw.sdp-prototype-etcd.default.svc:2380") != "http://92.242.132.24:2380"(resolved from "http://sdp-prototype-etcd-9s4hbbmmvw.sdp-prototype-etcd.default.svc:2380"))
```

This informs you that etcd tried to resolve its own address, and for
some reason got two different answers both times. Interestingly, the
`92.242.132.24` address is not actually in-cluster, but from the Internet,
and re-appears if we attempt to `ping` a nonexistent DNS name:

```console
$ ping does.not.exist
Pinging does.not.exist [92.242.132.24] with 32 bytes of data:
Reply from 92.242.132.24: bytes=32 time=25ms TTL=242
```

What is going on here is that that your ISP has installed a DNS server
that redirects unknown DNS names to a server showing a 'helpful' error
message complete with a bunch of advertisements. For some reason this
seems to cause a problem with Kubernetes' internal DNS resolution.

How can this be prevented? Theoretically it should be enough to force
the DNS server to one that does not have this problem (like Google's
`8.8.8.8` and `8.8.4.4` DNS servers), but that is tricky to get working.
Alternatively you can simply restart the entire thing until it works.
Unfortunately this is not quite as straightforward with `etcd-operator`,
as it sets the `restartPolicy` to `Never`, which means that any `etcd`
pod only gets once chance, and then will remain `Failed` forever. The
quickest way seems to be to delete the `EtcdCluster` object, then
`upgrade` the chart in order to re-install it:

```console
$ kubectl delete etcdcluster test-sdp-prototype-etcd
$ helm upgrade test sdp-prototype
```

This can generally be repeated until by pure chance the two DNS resolutions
return the same result and `etcd` starts up.
