# coding: utf-8
"""SDPSubarray device feature tests.

pytest-bdd generate <feature file name> .. <feature file nameN>

eg.

pytest-bdd generate 1_XR-7.feature

RUN with

docker run --rm -it -v $(pwd):/app/:rw --entrypoint=python skaorca/pytango_ska_dev -m pytest --gherkin-terminal-reporter -vv tests/steps

"""
from pytest_bdd import (
    given,
    scenarios,
    then,
    when
)

scenarios('../features/1_XR-7.feature')


# https://github.com/pytest-dev/pytest-bdd
# https://automationpanda.com/2018/10/22/python-testing-101-pytest-bdd/
# https://cucumber.io/docs/gherkin/reference/


@given('I have a subarray device')
def subarray_device(tango_context):
    """An initialised SDPSubarray device."""
    device = tango_context.device
    # TODO(BMo) Check that the device is initialised!
    return device


@when('I call the command assign resources')
def assign_resources(subarray_device):
    assert 'AssignResources' in subarray_device.get_command_list()
    # FIXME(BMo) for some reason cant call the command here ... \
    #            maybe the device is not initialised
    # result = subarray_device.AssignResources('')


@then('The obsState should be IDLE')
def obs_state_idle(subarray_device):
    assert 'obsState' in subarray_device.get_attribute_list()
    # obs_state_config = subarray_device.get_attribute_config('obsState')
    # print(obs_state_config)
    obs_state = subarray_device.obsState
    assert str(obs_state) == 'obsState.IDLE'
    # print(str(obs_state))
    # obs_state = subarray_device.read_attribute('obsState')
    # print(obs_state)


@then('The state should be ON')
def state_on(subarray_device):
    state = subarray_device.State()
    # assert str(state) == 'ON'
