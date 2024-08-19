import unittest
from werkzeug.datastructures import MultiDict
import shim.utils as utils

class UtilsTest(unittest.TestCase):
    def test_pagination_url_v3_to_v2(self):
        v3_url = "https://api.cf/v3/spaces?page=2&per_page=100"
        v2_params = MultiDict()
        v2_url = utils.pagination_url_v3_to_v2(v3_url, v2_params)
        self.assertEqual("/v2/spaces?order-direction=asc&page=2&results-per-page=100", v2_url)

        v3_url = "https://api.cf/v3/spaces?order_by=name&page=2&per_page=100"
        v2_params = MultiDict()
        v2_url = utils.pagination_url_v3_to_v2(v3_url, v2_params)
        self.assertEqual("/v2/spaces?order-by=name&order-direction=asc&page=2&results-per-page=100", v2_url)

        v3_url = "https://api.cf/v3/spaces?order_by=%2Bname&page=2&per_page=100"  # +name
        v2_params = MultiDict()
        v2_url = utils.pagination_url_v3_to_v2(v3_url, v2_params)
        self.assertEqual("/v2/spaces?order-by=name&order-direction=asc&page=2&results-per-page=100", v2_url)

        v3_url = "https://api.cf/v3/spaces?order_by=-name&page=2&per_page=100"
        v2_params = MultiDict()
        v2_url = utils.pagination_url_v3_to_v2(v3_url, v2_params)
        self.assertEqual("/v2/spaces?order-by=name&order-direction=desc&page=2&results-per-page=100", v2_url)

        v3_url = "https://api.cf/v3/spaces?order_by=-created_at&page=2&per_page=100"
        v2_params = MultiDict()
        v2_url = utils.pagination_url_v3_to_v2(v3_url, v2_params)
        self.assertEqual("/v2/spaces?order-direction=desc&page=2&results-per-page=100", v2_url)

        v3_url = "https://api.cf/v3/spaces?page=2&per_page=100"
        v2_params = MultiDict()
        v2_params["order-by"] = "id"
        v2_url = utils.pagination_url_v3_to_v2(v3_url, v2_params)
        self.assertEqual("/v2/spaces?order-by=id&order-direction=asc&page=2&results-per-page=100", v2_url)

        v3_url = "https://api.cf/v3/spaces?order_by=-created_at&page=2&per_page=100"
        v2_params = MultiDict()
        v2_params["order-by"] = "id"
        v2_url = utils.pagination_url_v3_to_v2(v3_url, v2_params)
        self.assertEqual("/v2/spaces?order-by=id&order-direction=desc&page=2&results-per-page=100", v2_url)

        v3_url = "https://api.cf/v3/spaces?order_by=name&page=2&per_page=100&names=s1,s2"
        v2_params = MultiDict()
        v2_params["q"] = "name IN s1,s2"
        v2_url = utils.pagination_url_v3_to_v2(v3_url, v2_params)
        self.assertEqual("/v2/spaces?order-by=name&order-direction=asc&page=2&q=name IN s1,s2&results-per-page=100", v2_url)

        v3_url = "https://api.cf/v3/spaces?order_by=name&page=2&per_page=100&names=s1,s2&organization_guids=o1"
        v2_params = MultiDict()
        v2_params["q"] = "name IN s1,s2"
        v2_params.add("q", "organization_guid:o1")
        v2_url = utils.pagination_url_v3_to_v2(v3_url, v2_params)
        self.assertEqual("/v2/spaces?order-by=name&order-direction=asc&page=2&q=name IN s1,s2&q=organization_guid:o1&results-per-page=100", v2_url)


    def test_pagination_params_v2_to_v3(self):
        v2_params = MultiDict()
        v3_params = utils.pagination_params_v2_to_v3(v2_params)
        self.assertEqual({}, v3_params)

        v2_params["results-per-page"] = "100"
        v2_params["page"] = "2"
        v3_params = utils.pagination_params_v2_to_v3(v2_params)
        self.assertEqual({"per_page": "100", "page": "2"}, v3_params)

        v2_params.clear()
        v2_params["order-direction"] = "asc"
        v3_params = utils.pagination_params_v2_to_v3(v2_params)
        self.assertEqual({}, v3_params)
        v2_params["order-direction"] = "desc"
        v3_params = utils.pagination_params_v2_to_v3(v2_params)
        self.assertEqual({"order_by": "-created_at"}, v3_params)

        v2_params.clear()
        v2_params["order-by"] = "id"
        v3_params = utils.pagination_params_v2_to_v3(v2_params)
        self.assertEqual({}, v3_params)
        v2_params["order-direction"] = "asc"
        v3_params = utils.pagination_params_v2_to_v3(v2_params)
        self.assertEqual({}, v3_params)
        v2_params["order-direction"] = "desc"
        v3_params = utils.pagination_params_v2_to_v3(v2_params)
        self.assertEqual({"order_by": "-created_at"}, v3_params)

        v2_params.clear()
        v2_params["order-by"] = "name"
        v3_params = utils.pagination_params_v2_to_v3(v2_params)
        self.assertEqual({"order_by": "name"}, v3_params)
        v2_params["order-direction"] = "asc"
        v3_params = utils.pagination_params_v2_to_v3(v2_params)
        self.assertEqual({"order_by": "name"}, v3_params)
        v2_params["order-direction"] = "desc"
        v3_params = utils.pagination_params_v2_to_v3(v2_params)
        self.assertEqual({"order_by": "-name"}, v3_params)

    def test_filter_params_v2_to_v3(self):
        v2_params = MultiDict()
        v3_params = utils.filter_params_v2_to_v3(v2_params)
        self.assertEqual({}, v3_params)

        v2_params.add("q", "name:s1")
        v3_params = utils.filter_params_v2_to_v3(v2_params)
        self.assertEqual({"names": "s1"}, v3_params)

        v2_params.clear()
        v2_params.add("q", "organization_guid:o1")
        v3_params = utils.filter_params_v2_to_v3(v2_params)
        self.assertEqual({"organization_guids": "o1"}, v3_params)

        v2_params.clear()
        v2_params.add("q", "name IN s1,s2")
        v2_params.add("q", "organization_guid:o1")
        v3_params = utils.filter_params_v2_to_v3(v2_params)
        self.assertEqual({"names": "s1,s2", "organization_guids": "o1"}, v3_params)