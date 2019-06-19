# Install and Setup Kubernetes

First, login as ‘sudo’ user because the following set of commands need to 
be executed with ‘sudo’ permissions. Then, update your ‘apt-get’ repository.

```bash
sudo su
apt-get update
```

Turn Off Swap Space
Next, we have to turn off the swap space because Kubernetes will start 
throwing random errors otherwise. After that you need to open the ‘fstab’ file 
and comment out the line which has mention of swap partition.

```bash
swapoff -a
nano /etc/fstab
```

## Install OpenSSH-Server
Now we have to install openshh-server. Run the following command:

```bash
sudo apt-get install openssh-server
```

## Install Docker

Now we have to install Docker because Docker images will be used for managing 
the containers in the cluster. If you have docker installed skip this.
Run the following commands:

```bash
sudo su
apt-get update 
apt-get install -y docker.io
```

Next we have to install these 3 essential components for setting up Kubernetes
environment: kubeadm, kubectl, 

Run the following commands before installing the Kubernetes environment.

```bash
apt-get update && apt-get install -y apt-transport-https curl
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb http://apt.kubernetes.io/ kubernetes-xenial main
EOF
apt-get update
apt-get install -y kubelet kubeadm kubectl
```

## Updating Kubernetes Configuration

Next, we will change the configuration file of Kubernetes. Run the following command:

# nano /etc/systemd/system/kubelet.service.d/10-kubeadm.conf

This will open a text editor, enter the following line after the last “Environment Variable”:

```text
Environment=”cgroup-driver=systemd/cgroup-driver=cgroupfs”
```

## Steps Only For Kubernetes Master VM (kmaster)

```bash
kubeadm init --apiserver-advertise-address=<ip-address-of-kmaster-vm> --pod-network-cidr=192.168.0.0/16
```

Run the commands from the above output as a non-root user

```bash
$ mkdir -p $HOME/.kube
$ sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
$ sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

To verify, if kubectl is working or not, run the following command:

```bash
kubectl get pods -o wide --all-namespaces
```
or
```bash
kubectl version --short 
```

## For Only Kubernetes Node VM (knode)
To join the cluster! This is probably the only step that you will be doing on 
the node, after installing kubernetes on it.

Run the join command that you saved, when you ran ‘kubeadm init’ command on the master.

# Migrate from Docker to Kubernetes

What’s Kompose? It’s a conversion tool for all things compose (namely Docker Compose) 
to container orchestrator.

```bash
curl -L https://github.com/kubernetes/kompose/releases/download/v1.16.0/kompose-linux-amd64 -o kompose
chmod +x kompose
sudo mv ./kompose /usr/local/bin/kompose
```

Example docker-compose.yml file available in  this directory.

Run the kompose up command to deploy to Kubernetes directly, or skip to the 
next step instead to generate a file to use with kubectl.

To convert the docker-compose.yml file to files that you can use with kubectl, 
run kompose convert and then kubectl apply -f <output file>

```bash
kompose convert
kubectl apply -f frontend-service.yaml,redis-master-service.yaml,redis-slave-service.yaml,
frontend-deployment.yaml,redis-master-deployment.yaml,redis-slave-deployment.yaml
```
Once you have deployed “composed” application to Kubernetes, 
$ kompose down will help you to take the application out by deleting its deployments and services. 

