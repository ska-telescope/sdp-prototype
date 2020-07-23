# PSS Receive Workflow

This is a simple python code for a PSS (Pulsar Search Sub-element) receiver
capable of receiving UDP-based SPEAD streams.

## Dependencies

- Numpy>=1.16.2 : https://numpy.org/
- SPEAD2==2.0.2 : https://spead2.readthedocs.io/en/latest/

## Description

There are two simple python programmes (receive and send). The sender is a dummy sender that is capable of loading
a single-pulse search candidate file and sending the contents of that file, with some dummy metadata over UDP.
The receiver listens for these UDP streams and terminates once they are received.

## Running send and receive standalone

To demonstrate their functionality it is possible to run the send and receive codes natively.

### Start the receiver

```bash
    cd [sdp-prototype]/src/pss_receive/pss-receive
    python receive.py
```

The console will show that the receiver is listening on port 9012

```bash
    $ python receive.py
    Listening on port 9021..
```

### Start the sender

We are sending the contents of a single pulse search candidate file test.spccl. In a separate terminal...

```bash
    cd [sdp-prototype]/src/pss_receive/pss-send
    python send.py -f test.spccl
```

The console will show some details of the data that we've send.

```bash
    $ python send.py -f test.spccl
    INFO 2020-02-03 13:32:36,595 Start of stream
    INFO 2020-02-03 13:32:36,595 Sending stream with id=EEK8V39g0JEP5Dmh, name=test.spccl
    INFO 2020-02-03 13:32:36,595 Sending stream with id=EEK8V39g0JEP5Dmh, nbytes=5421
    INFO 2020-02-03 13:32:36,595 Sending stream with id=EEK8V39g0JEP5Dmh, nlines=34
    INFO 2020-02-03 13:32:36,595 End of stream
    File test.spccl sent
```

Returning to the terminal in which we started the receiver we should see the data sent by send.py. The data has been
saved to a file in the subdirectory 'output'.

## Deploying receive as an sdp component

These instructions assume you have created the etcd cluster and deployed the sdp components. In other words, in the instructions
for ''Running the SDP Prototype stand-alone'', you have done everything up to, but not including, the ''start a worflow'' section.

Now we add a pss\_receive processing block to the configuration database. We first connect to a console pod which allows us to interact with the configuration database. 


```bash
    $ kubectl exec -it deploy/sdp-prototype-console -- /bin/bash
    $ sdpcfg process realtime:pss_receive:0.1.0
    OK, pb_id = realtime-20200203-0000
```

We can watch the tasks that are being deployed in the sdp namespace by running..

```bash
    $ kubectl get all -n sdp
    NAME                                                   READY   STATUS              RESTARTS   AGE
    pod/pss-receive-6p2dx                                  0/1     ContainerCreating   0          45s
    pod/realtime-20200203-0000-workflow-78fb74d48d-f6pgm   1/1     Running             0          56s

    NAME                  TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)    AGE
    service/pss-receive   ClusterIP   10.96.224.5   <none>        9021/UDP   45s

    NAME                                              READY   UP-TO-DATE   AVAILABLE   AGE
    deployment.apps/realtime-20200203-0000-workflow   1/1     1            1           56s

    NAME                                                         DESIRED   CURRENT   READY   AGE
    replicaset.apps/realtime-20200203-0000-workflow-78fb74d48d   1         1         1       57s

    NAME                    COMPLETIONS   DURATION   AGE
    job.batch/pss-receive   0/1           46s        46s
```

...in which we see the workflow pod, created by the processing controller and the receive pod. Looking at the logs of the
processing controller we can see that processing block realtime-20200203-0000 has been deployed and is in a 'waiting' state
as we haven't sent it any data yet.

```bash
    $ kubectl logs sdp-prototype-processing-controller-[...]
    processing_controller.py#105||('pss_receive', '0.1.0'): nexus.engageska-portugal.pt/sdp-prototype/workflow-pss-receive:0.1.0
    processing_controller.py#106||Batch workflows:
    processing_controller.py#158||Current PBs: ['realtime-20200203-0000']
    processing_controller.py#159||Current deployments: ['realtime-20200203-0000-pss-receive', 'realtime-20200203-0000-workflow']
    processing_controller.py#160||Current PBs with deployment: ['realtime-20200203-0000']
    processing_controller.py#207||Waiting...
```

Looking at the output of the workflow pod in the sdp namespace we can see that the processing controller has claimed the processing
block and deployed the pss-receive container.

```bash
    $ kubectl logs realtime-20200203-0000-workflow-[...] -n sdp
    INFO:pss_recv:Claimed processing block ProcessingBlock(pb_id='realtime-20200203-0000',
         sbi_id=None, workflow={'id': 'pss_receive', 'type': 'realtime', 'version': '0.1.0'},
         parameters={}, scan_parameters={})
    INFO:pss_recv:Deploying PSS Receive...
    INFO:pss_recv:Done, now idling...
```

Finally, we can see the output of the receive pod, which shows the same console output as would be seen
were we to be running the receive code standalone.

```bash
    $ kubectl logs pss-receive-[...] -n sdp
    Listening on port 9021..
```

### Sending some data

```bash
    $ cd [sdp-prototype]/src/pss_receive/pss-send
```

In this directory there is a K8s deployment manifest that will start a send job in the sdp namespace. To do this..

```bash
    $ kubectl apply -f deploy-sender.yaml -n sdp
    job.batch/sender created
```

Looking at the logs in the sdp namespace we see that..

- A sender pod was created and has completed
- The receiver pod shows as completed
- A sender job has been deployed under 'jobs'

```bash
    $  kubectl get all -n sdp
    NAME                                                   READY   STATUS      RESTARTS   AGE
    pod/pss-receive-q6dpd                                  0/1     Completed   0          27s
    pod/realtime-20200203-0000-workflow-78fb74d48d-662rb   1/1     Running     0          33s
    pod/sender-rvxgh                                       0/1     Completed   0          11s

    NAME                  TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
    service/pss-receive   ClusterIP   10.96.242.53   <none>        9021/UDP   27s

    NAME                                              READY   UP-TO-DATE   AVAILABLE   AGE
    deployment.apps/realtime-20200203-0000-workflow   1/1     1            1           33s

    NAME                                                         DESIRED   CURRENT   READY   AGE
    replicaset.apps/realtime-20200203-0000-workflow-78fb74d48d   1         1         1       33s

    NAME                    COMPLETIONS   DURATION   AGE
    job.batch/pss-receive   1/1           19s        27s
    job.batch/sender        1/1           3s         11s
```

As before, looking at the logs for the sender and receiver pods, we can see the data that was sent/received.

### Tidying up

Now we can stop the sender job and remove the processing block from the configuration

```bash
    $ sdpcfg delete /pb/realtime-20200203-0000
    $ kubectl delete job sender -n sdp
```

# Deploying the SDP via TANGO

(More generalised documentation can be found at https://developer.skatelescope.org/projects/sdp-prototype/en/latest/running/running\_standalone.html#accessing-tango

Connect to the TANGO interface

```bash
    kubectl exec -it itango-tango-base-sdp-prototype -- /venv/bin/itango3
```

Create an interface to the SDP-subarray-1 TANGO device

```bash
    d = DeviceProxy('mid_sdp/elt/master')
```

We can check the obsState of the sub-array which is currently IDLE.

```bash
    d.obsState
```

We can then set the configuration of the Scheduling Block Instance by defining a JSON string containing information about the scan parameters and the workflow(s) to be deployed.

```bash
   config = '''
   {
  "id": "sbi-test-20200715-00000",
  "max_length": 600.0,
  "scan_types": [
    {
      "id": "science",
      "channels": [
        {"count": 372, "start": 0, "stride": 2, "freq_min": 0.35e9, "freq_max": 0.358e9, "link_map": [[0,0], [200,1]]}
      ]
    }
  ],
  "processing_blocks": [
    {
      "id": "pb-test-20200715-00000",
      "workflow": {"type": "realtime", "id": "test_receive_addresses", "version": "0.3.2"},
      "parameters": {}
    },
    {
      "id": "pb-test-20200715-00001",
      "workflow": {"type": "realtime", "id": "pss_receive", "version": "0.2.0"},
      "parameters": {}
    }
  ]
}'''
```

In this case the workflows are test\_receive\_addresses and pss\_receive.  If we look at the processes that are running in the sdp namespace we can see that the two workflows have been deployed and the pss-receive workflow has deployed the pss-receive container (the test\_receive\_addresses workflow does not trigger any deployments). 

```bash
    [bshaw@dokimi ~]$ kubectl get all -n sdp 
    NAME                                             READY   STATUS    RESTARTS   AGE
    pod/proc-pb-test-20200715-00000-workflow-dm48x   1/1     Running   0          2m
    pod/proc-pb-test-20200715-00001-workflow-j8kbj   1/1     Running   0          2m
    pod/pss-receive-sbwxz                            1/1     Running   0          1m

    NAME                  TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
    service/pss-receive   ClusterIP   10.96.84.108   <none>        9021/UDP   1m

    NAME                                             COMPLETIONS   DURATION   AGE
    job.batch/proc-pb-test-20200715-00000-workflow   0/1           42m        2m
    job.batch/proc-pb-test-20200715-00001-workflow   0/1           42m        2m
    job.batch/pss-receive 
```
We can then set the scan type using the Configure() method. 

```bash
   d.Configure('{"scan_type": "science"}')
```

At this point our subarray has entered a READY state. We then set the scan running with the Scan() method. 

```bash
   d.Scan('{"id": 1}')
```

Now the subarray has entered a SCANNING state and data is being acquired. We can emulate the flow of data into the SDP from PSS by deployed the dummer sender by the same method as above. In a separate terminal, 

```bash
   cd /[...]/sdp-prototype/src/pss_receive/pss-send
   kubectl apply -f deploy-sender.yaml
```

This will deploy a sender job (called sender) into the sdp namespace. This has sent some candidate data to the receiver, after which both the sender and receiver enter a "completed" state. 

```bash
    [bshaw@dokimi ~]$ kubectl get all -n sdp
    NAME                                             READY   STATUS      RESTARTS   AGE
    pod/proc-pb-test-20200715-00000-workflow-dm48x   1/1     Running     0          71m
    pod/proc-pb-test-20200715-00001-workflow-j8kbj   1/1     Running     0          71m
    pod/pss-receive-sbwxz                            0/1     Completed   0          69m
    pod/sender-jrm6t                                 0/1     Completed   0          4m37s

    NAME                  TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
    service/pss-receive   ClusterIP   10.96.84.108   <none>        9021/UDP   69m

    NAME                                             COMPLETIONS   DURATION   AGE
    job.batch/proc-pb-test-20200715-00000-workflow   0/1           71m        71m
    job.batch/proc-pb-test-20200715-00001-workflow   0/1           71m        71m
    job.batch/pss-receive                            1/1           64m        69m
    job.batch/sender 
```

Now we can end the scan

```bash
   d.EndScan()
```

and the subarray reverts to the READY state. We then clear the scan-type with.

```bash
    d.Reset()
```

and the subarray returns to the IDLE state.  The SDP resources can then be freed using 

```bash
   d.ReleaseResources()
```

which sets the workflows into a "completed" state. 

## Ongoing work

