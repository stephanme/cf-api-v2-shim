import logging
import requests
import unittest
import os
import json
from typing import Any, Tuple
from deepdiff import DeepDiff
import pprint

# configure logging before initializing further modules
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
# logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# read config file, global for all shim tests
test_config_file = f"{os.path.dirname(__file__)}/testconfig.json"
test_config = {}
if os.path.isfile(test_config_file):
    with open(test_config_file, "r") as f:
        test_config = json.load(f)


class ShimTestCase(unittest.TestCase):
    session = None

    # one-time initialization for all ShimTests
    # MUST be called by setUpClass of all subclasses
    @classmethod
    def setUpClass(cls):
        if not cls.session:
            cls.cfapi_url = test_config["cfapi_url"]
            cls.uaa_url = test_config["uaa_url"]
            cls.shim_url = test_config["shim_url"]
            cls.username = test_config["username"]
            cls.password = test_config["password"]
            cls.org_name = test_config["org_name"]
            cls.space_name = test_config["space_name"]
            cls.session = requests.Session()

            token_res = cls.session.post(
                f"{cls.uaa_url}/oauth/token",
                data={
                    "client_id": "cf",
                    "client_secret": "",
                    "grant_type": "password",
                    "username": cls.username,
                    "password": cls.password,
                },
            )
            token_res.raise_for_status()
            token = token_res.json()["access_token"]
            cls.session.headers.update({"Authorization": f"Bearer {token}"})
            res = cls.session.get(f"{cls.cfapi_url}/v3/users", params={
                "usernames": cls.username
            })
            res.raise_for_status()
            cls.user_guid = res.json()["resources"][0]["guid"]

            # guids for test resources set-up by ./resources/setup.sh
            res = cls.session.get(f"{cls.cfapi_url}/v3/organizations?names={cls.org_name}")
            res.raise_for_status()
            cls.org_guid = res.json()["resources"][0]["guid"]
            res = cls.session.get(f"{cls.cfapi_url}/v3/spaces?names={cls.space_name}")
            res.raise_for_status()
            cls.space_guid = res.json()["resources"][0]["guid"]
            res = cls.session.get(
                f"{cls.cfapi_url}/v3/apps",
                params={
                    "space_guids": cls.space_guid,
                    "order_by": "name",
                },
            )
            res.raise_for_status()
            apps = res.json()["resources"]
            cls.app1_guid = apps[0]["guid"]
            cls.app2_guid = apps[1]["guid"]
            cls.app3_guid = apps[2]["guid"]
            cls.app4_guid = apps[3]["guid"]


    def run_v2_shim_get(self, endpoint: str, expected_status=200) -> Tuple[Any, Any]:
        v2_res = self.session.get(f"{ShimTestCase.cfapi_url}{endpoint}")
        shim_res = self.session.get(f"{ShimTestCase.shim_url}{endpoint}")
        logger.debug(f"Testing {endpoint}: shim={shim_res.elapsed.total_seconds()} s, v2={v2_res.elapsed.total_seconds()} s")
        self.assertEqual(expected_status, v2_res.status_code)
        self.assertEqual(expected_status, shim_res.status_code)
        return v2_res.json(), shim_res.json()

    # a better way to compare dicts
    def assertDict(self, first: dict, second: dict):
        diff = DeepDiff(first, second, verbose_level=2)
        if len(diff) > 0:
            logger.error(pprint.pformat(diff))
        self.assertEqual(diff, {})
