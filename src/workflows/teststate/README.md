# Propagation of error from workflow to PB state in configuration database

## Introduction

This workflow propagates Processing block states and adds it to the configuration database.


It uses following functions to get create, get and update PB states in the configuration database:
```bash
pb_state = txn.get_processing_block_state(pb_id)
txn.create_processing_block_state(pb_id, pb_state)
txn.update_processing_block_state(pb_id, pb_state)
```

It follows the following schema. Schema is not currently checked in but some point it will be, so better to follow it.

```html
https://gitlab.com/ska-telescope/sdp-prototype/blob/master/src/config_db/SCHEMA.md
```

## Testing

It creates a workflow and creates the processing block states and loops around for 3 minutes and then updates 
the processing block state with an error state. 

Assuming kubernetes and helm is configured and etcd operator is deployed. Instructions on how to do this can 
be found in deploy/charts directory.

Before installing the sdp-prototype chart, need to create sdp namespace

```bash
kubectl create namespace sdp
```

Install sdp-prototype chart

```bash
microk8s.helm install sdp-prototype -n sdp-prototype --set helm_deploy.chart_repo.ref=SIM-208/processing-controller
```
Make sure you find the appropriate command if using minikube.
Also, once the processing controller branch is merged to master, not required to set helm_Deploy.chat_repo...

### Connecting to configuration database

Set the environment variable SDP_CONFIG_PORT according to the second part of the PORTS(S) column:

```
export SDP_CONFIG_PORT=32234
```

For Minikube, you need to set both SDP_CONFIG_HOST and SDP_CONFIG_PORT and for microk8s just set SDP_CONFIG_PORT

This will allow you to connect with the sdpcfg utility:

```bash
$ pip install -U ska-sdp-config
$ sdpcfg ls -R /
```
Keys with / prefix:
Which correctly shows that the configuration is currently empty.

Start a workflow

```bash
sdpcfg process realtime:teststate:0.2.0
```

Check if the processing block has been added to the configuration database and the states has been created

```bash
sdpcfg ls values -R /
```

Logs of the pods can be checked by running the following command

```bash
microk8s.kubectl logs <podname> -n sdp
```

After 3 minutes, check the the database again and you will notice that the state has been changed to 'error'
```bash
sdpcfg ls values -R /
```


### TO DO:

- Use kubernetes API to get actual state of the pod.
- Think about better way to test.