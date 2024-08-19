import logging
from tests.shimtest import ShimTestCase

logger = logging.getLogger(__name__)


class RootTest(ShimTestCase):
    @classmethod
    def setUpClass(cls):
        ShimTestCase.setUpClass()

    def test_root(self):
        (v2_json, shim_json) = self.run_v2_shim_get("/")

        self.assertEqual(shim_json["links"]["self"]["href"], RootTest.shim_url)
        self.assertEqual(shim_json["links"]["cloud_controller_v2"]["href"], f"{RootTest.shim_url}/v2")

        self.assertEqual(v2_json["links"]["cloud_controller_v2"]["href"], f"{RootTest.cfapi_url}/v2")

        del shim_json["links"]["self"]["href"]
        del shim_json["links"]["cloud_controller_v2"]["href"]
        del shim_json["links"]["cloud_controller_v3"]["href"]
        del v2_json["links"]["self"]["href"]
        del v2_json["links"]["cloud_controller_v2"]["href"]
        del v2_json["links"]["cloud_controller_v3"]["href"]
        self.assertDict(v2_json, shim_json)

    # as example of a proxied endpoint
    def test_v2_info(self):
        (v2_json, shim_json) = self.run_v2_shim_get("/v2/info")
        self.assertDict(v2_json, shim_json)
