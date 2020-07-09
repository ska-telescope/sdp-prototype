### Delivery workflow

This workflow provides a basic implementation of an SDP Delivery mechanism. It
uploads data from SDP buffer reservations to Google Cloud Platform (GCP). It
uses Dask as an execution engine.

#### Parameters

The workflow parameters are:

* `bucket`: name of the GCP storage bucket in which to upload the data
* `buffers`: list of buffers to upload to the storage bucket, each contains
    * `name`: name of the buffer reservation
    * `destination`: location to upload it in the bucket
* `service_account`: location of the GCP service account key (stored in a
  Kubernetes secret)
    * `secret`: name of the secret
    * `file`: filename of the service account key
* `n_workers`: number of Dask workers to deploy

For example:

```json
{
  "bucket": "delivery-test",
  "buffers": [
    {
      "name": "buff-pb-20200523-00000-test",
      "destination": "buff-pb-20200523-00000-test"
    }
  ],
  "service_account": {
    "secret": "delivery-gcp-service-account",
    "file": "service-account.json"
  },
  "n_workers": 1
}
```

#### Creating a GCP storage bucket to receive the data

The steps to create a GCP storage bucket for the delivery workflow are as
follows. GCP has ample documentation, so each step is linked to the relevant
section:

1) [Create a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects).
2) [Create a storage bucket in the project](https://cloud.google.com/storage/docs/creating-buckets).
3) [Create a service account and download a key](https://cloud.google.com/iam/docs/creating-managing-service-accounts):

    * The service account must have the role "Storage Object Creator".
    * Create and download a key in JSON format.

#### Adding the GCP service account key as a Kubernetes secret

To make the service account key available to the delivery workflow, it needs to
be uploaded to the cluster as a Kubernetes secret. The command to do this is:

```console
kubectl create secret generic <secret-name> --from-file=<service-account-key> -n <sdp-namespace>
```

Using the values from the example parameters above and assuming the namespace
for the SDP dynamic deployments is `sdp` (the default), the command would be:

```console
kubectl create secret generic delivery-gcp-service-account --from-file=service-account.json -n sdp
```

To check the secret has been created, you can use the command:

```console
kubectl describe secret delivery-gcp-service-account -n sdp
```

and the output should look like:

```console
Name:         delivery-gcp-service-account
Namespace:    sdp
Labels:       <none>
Annotations:  <none>

Type:  Opaque

Data
====
service-account.json:  2382 bytes
```
