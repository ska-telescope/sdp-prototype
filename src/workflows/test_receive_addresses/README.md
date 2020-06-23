## Test Receive Addresses Workflow
 
### Introduction
The purpose of this workflow is to test the mechanism for generating SDP receive addresses 
from the channel link map for each scan type which is contained in the list of scan types 
in the SB. The workflow picks it up from there, uses it to generate the receive addresses 
for each scan type and writes them to the processing block state. It consists of a map
of scan type to a receive address map. This address map get publishes to the appropriate 
attribute once the SDP subarray finishes the transition following AssignResources.
    
    
### Testing
First checkout the branch, create a file called test.yaml inside the charts directory and add:
```
tangods:
  subarray:
    version: 0.9.2-<git-hash>
```

where is the latest git hash of the branch. Then install the prototype with (Helm 3 syntax):

```bash
helm install test sdp-prototype -f test.yaml \                                                    
  --set processing_controller.workflows.url=https://gitlab.com/ska-telescope/sdp-prototype/raw/receive-addresses-hack/src/workflows/workflows.json
```

Once all the pods are the running. Connect to the Tango interface using the following command:

```
kubectl exec -it itango-tango-base-test /venv/bin/itango3
```

Obtain a handle to the device with:

```
d = DeviceProxy('mid_sdp/elt/subarray_1')
```


Here is the configuration string for the scheduling block instance:

```
config = '''
{
  "id": "sbi-mvp01-20200318-0001",
  "max_length": 21600.0,
  "scan_types": [
     {
       "id": "science_A",
       "coordinate_system": "ICRS", "ra": "02:42:40.771", "dec": "-00:00:47.84",
       "channels": [{
          "count": 744, "start": 0, "stride": 2, "freq_min": 0.35e9, "freq_max": 0.368e9, "link_map": [[0,0], [200,1], [744,2], [944,3]]
       },{
          "count": 744, "start": 2000, "stride": 1, "freq_min": 0.36e9, "freq_max": 0.368e9, "link_map": [[2000,4], [2200,5]]
       }]
     },
     {
       "id": "calibration_B",
       "coordinate_system": "ICRS", "ra": "12:29:06.699", "dec": "02:03:08.598",
       "channels": [{
          "count": 744, "start": 0, "stride": 2, "freq_min": 0.35e9, "freq_max": 0.368e9, "link_map": [[0,0], [200,1], [744,2], [944,3]]
       },{
          "count": 744, "start": 2000, "stride": 1, "freq_min": 0.36e9, "freq_max": 0.368e9, "link_map": [[2000,4], [2200,5]]
       }]
     }
   ],
  "processing_blocks": [
    {
      "id": "pb-mvp01-20200318-0001",
      "workflow": {"type": "realtime", "id": "test_receive_addresses", "version": "0.3.2"},
      "parameters": {}
    },
    {
      "id": "pb-mvp01-20200318-0002",
      "workflow": {"type": "realtime", "id": "test_realtime", "version": "0.2.0"},
      "parameters": {}
    }
  ]
} '''
```

Start the scheduling block instance by the AssignResources command:

```
d.AssignResources(config)
```

You can connect to the configuration database by running the following command: 

``` kubectl exec -it deploy/test-sdp-prototype-console bash ``` and from there to see the full list run ```sdpcfg ls -R /```

To check if the receive addresses are updated in the processing block state correctly, run the following command: 

```
sdpcfg list values /pb/pb-mvp01-20200318-0001/state
``` 

and the output should look like this:

```
/pb/pb-mvp01-20200318-0001/state = {
  "receive_addresses": {
    "calibration_B": {
      "host": [
        [
          0,
          "192.168.0.1"
        ],
        [
          2000,
          "192.168.0.1"
        ]
      ],
      "port": [
        [
          0,
          9000,
          1
        ],
        [
          2000,
          9000,
          1
        ]
      ]
    },
    "science_A": {
      "host": [
        [
          0,
          "192.168.0.1"
        ],
        [
          2000,
          "192.168.0.1"
        ]
      ],
      "port": [
        [
          0,
          9000,
          1
        ],
        [
          2000,
          9000,
          1
        ]
      ]
    }
  },
  "resources_available": true,
  "status": "RUNNING"
}
```

To access the SBI run this ```sdpcfg list values /sb/sbi-mvp01-20200318-0001```

In there you should see that pb_receive_addresses is updated with the PB_ID.

This should now update the receiveAddresses attribute with receive addresses map
and that can be verified by running d.receiveAddresses and the output should look like this:

```
Out[4]: '{"calibration_B": {"host": [[0, "192.168.0.1"], [2000, "192.168.0.1"]], "port": [[0, 9000, 1], [2000, 9000, 1]]}, "science_A": {"host": [[0, "192.168.0.1"], [2000, "192.168.0.1"]], "port": [[0, 9000, 1], [2000, 9000, 1]]}}'
```