# Instructions to run Visibility Receiver helm chart

```bash
sudo minikube start --vm-driver=none --memory 4096mb
sudo helm init
cd deploy/charts
sudo helm install vis-receive -n vis-receive  
sudo kubectl get pod --watch
```

```bash
sudo kubectl logs <name>
```

The output should look like this

```text
Running RECV_VERSION 0.1.0
 + Number of system CPU cores  : 2
 + Number of SPEAD streams     : 1
 + Number of receiver threads  : 0
 + Number of writer threads    : 8
 + Number of times in buffer   : 8
 + Maximum number of buffers   : 2
 + UDP port range              : 41000-41000
 + Number of channels per file : 1
 + Output root                 : (null)
Requested socket buffer of 16777216 bytes; actual size is 212992 bytes
All 1 stream(s) completed.
```