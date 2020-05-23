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

Now we add a pss\_receive processing block to the configuration database.

```bash
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

## Ongoing work

