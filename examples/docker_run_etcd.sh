#!/bin/sh

docker run -d -h etcd --name etcd \
    -P \
    quay.io/coreos/etcd:latest \
    /usr/local/bin/etcd \
    --advertise-client-urls=http://etcd:2379 \
    --listen-client-urls=http://0.0.0.0:2379 \
    --initial-advertise-peer-urls=http://etcd:2380 \
    --listen-peer-urls=http://0.0.0.0:2380 \
    --initial-cluster=default=http://etcd:2380 $* || exit 1

ETCDCTL_ENDPOINTS=`docker port etcd 2379`
SDP_CONFIG_PORT=`echo $ETCDCTL_ENDPOINTS | sed 's/.*://'`
SDP_CONFIG_HOST=`echo $ETCDCTL_ENDPOINTS | sed 's/:.*//'`

echo
echo Etcd container is running. Test by going:
echo  $ docker run --link etcd --env ETCDCTL_ENDPOINTS=etcd:2379 --env ETCDCTL_API=3 -i quay.io/coreos/etcd:latest /usr/local/bin/etcdctl endpoint health
echo  $ ETCDCTL_ENDPOINTS=$ETCDCTL_ENDPOINTS ETCDCTL_API=3 etcdctl endpoint health
echo "(use second version if you have etcdctl installed locally)"
echo
echo To use with ska-sdp-config, either link into container, or use locally:
echo  $ docker run --link etcd --env SDP_CONFIG_HOST=etcd ...
echo  $ SDP_CONFIG_HOST=$SDP_CONFIG_HOST SDP_CONFIG_PORT=$SDP_CONFIG_PORT sdpcfg ...

