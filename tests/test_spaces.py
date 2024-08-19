import logging
from tests.shimtest import ShimTestCase

# import pprint

logger = logging.getLogger(__name__)


class SpacesTest(ShimTestCase):
    @classmethod
    def setUpClass(cls):
        ShimTestCase.setUpClass()

    def test_v2_get_space(self):
        endpoint = f"/v2/spaces/{SpacesTest.space_guid}"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)

    def test_v2_get_space_404(self):
        endpoint = f"/v2/spaces/00000000-0000-0000-0000-000000000000"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint, expected_status=404)
        # TODO: self.assertDict(v2_json, shim_json) - error response mapping

    def test_v2_get_spaces(self):
        endpoint = f"/v2/spaces"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)
        endpoint = f"/v2/spaces?results-per-page=1"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)

    def test_v2_get_spaces_asc(self):
        endpoint = f"/v2/spaces?order-direction=asc"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)
        endpoint = f"/v2/spaces?order-direction=asc&results-per-page=1"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)

    def test_v2_get_spaces_desc(self):
        endpoint = f"/v2/spaces?order-direction=desc"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)
        endpoint = f"/v2/spaces?order-direction=desc&results-per-page=1"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)

    def test_v2_get_spaces_orderby_id(self):
        endpoint = f"/v2/spaces?order-by=id&page=1"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)
        endpoint = f"/v2/spaces?order-by=id&page=1&results-per-page=1"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)

    def test_v2_get_spaces_orderby_id_desc(self):
        endpoint = f"/v2/spaces?order-by=id&order-direction=desc"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)
        endpoint = f"/v2/spaces?order-by=id&order-direction=desc&results-per-page=1"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)

    def test_v2_get_spaces_orderby_name(self):
        endpoint = f"/v2/spaces?order-by=name"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)
        endpoint = f"/v2/spaces?order-by=name&results-per-page=1"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)

    def test_v2_get_spaces_orderby_name_desc(self):
        endpoint = f"/v2/spaces?order-by=name&order-direction=desc"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)
        endpoint = f"/v2/spaces?order-by=name&order-direction=desc&results-per-page=1"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)

    def test_v2_get_spaces_q_org_guid(self):
        endpoint = f"/v2/spaces?q=organization_guid:{SpacesTest.org_guid}"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)

    def test_v2_get_spaces_q_name(self):
        endpoint = f"/v2/spaces?q=name:{SpacesTest.space_name}"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)

    def test_v2_get_spaces_q_app_guid(self):
        endpoint = f"/v2/spaces?q=app_guid IN {SpacesTest.app1_guid},{SpacesTest.app2_guid}"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)

    def test_v2_get_spaces_q_developer_guid(self):
        endpoint = f"/v2/spaces?q=developer_guid:{SpacesTest.user_guid}"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)
