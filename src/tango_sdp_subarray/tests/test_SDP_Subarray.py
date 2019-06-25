from pytest_bdd import scenario, given, when, then

@scenario('1_XR-7.feature', 'Scanning')
def test_scanning():
    pass

@given('a Ready SDP State Device')
def test_device():
    device = SDP_Subarray.init_device()
    #I know this won't really set up a suitable device, but...

@when('the SDP State Device recieves the Run command')


@then('the SDP State Device will transition to the Scanning State')
