import logging
from tests.shimtest import ShimTestCase

logger = logging.getLogger(__name__)


class StacksTest(ShimTestCase):
    @classmethod
    def setUpClass(cls):
        res = cls.config.session.get(f"{cls.config.cfapi_url}/v3/stacks?default=true")
        cls.default_stack_guid = res.json()["resources"][0]["guid"]

    def test_v2_get_stack(self):
        (v2_json, shim_json) = self.run_v2_shim_get(f"/v2/stacks/{StacksTest.default_stack_guid}")
        self.assertDict(v2_json, shim_json)

    def test_v2_get_stacks(self):
        (v2_json, shim_json) = self.run_v2_shim_get("/v2/stacks")
        self.assertDict(v2_json, shim_json)

        (v2_json, shim_json) = self.run_v2_shim_get("/v2/stacks?results-per-page=1")
        self.assertDict(v2_json, shim_json)

        (v2_json, shim_json) = self.run_v2_shim_get("/v2/stacks?results-per-page=1&page=2")
        self.assertDict(v2_json, shim_json)

        (v2_json, shim_json) = self.run_v2_shim_get("/v2/stacks?results-per-page=1&order-direction=desc")
        self.assertDict(v2_json, shim_json)

        (v2_json, shim_json) = self.run_v2_shim_get("/v2/stacks?q=name:cflinuxfs4")
        self.assertDict(v2_json, shim_json)

        (v2_json, shim_json) = self.run_v2_shim_get("/v2/stacks?q=name IN cflinuxfs4,cflinuxfs3")
        self.assertDict(v2_json, shim_json)

        (v2_json, shim_json) = self.run_v2_shim_get("/v2/stacks?inline-relations-depth=2")  # not relevant for stacks
        self.assertDict(v2_json, shim_json)
