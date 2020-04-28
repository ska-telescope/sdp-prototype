from processing_controller import processing_controller
import workflows_test

# This needs to handle transactions properly...
class MemoryBackend:
    def __init__(self):
        self.dict = {}

    def lease(self, ttl):
        return None

    def txn(self, **kwargs):
        return self.dict


def test_stuff():
    controller = processing_controller.ProcessingController(workflows_test.SCHEMA,
                                                            workflows_test.WORK_URL, 1)
    controller._workflows.update_url = controller._workflows.update_file

    # FIXME: needs an update to sdp_config to properly support backend injection.
    #controller.main(backend=MemoryBackend())
