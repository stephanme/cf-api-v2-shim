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

# read config file
test_config_file = f"{os.path.dirname(__file__)}/testconfig.json"
test_config = {}
if os.path.isfile(test_config_file):
    with open(test_config_file, "r") as f:
        test_config = json.load(f)


# TODO: read from private config file (credentials)
class ITsConfig:
    def __init__(self):
        self.cfapi_url = test_config["cfapi_url"]
        self.uaa_url = test_config["uaa_url"]
        self.shim_url = test_config["shim_url"]
        self.username = test_config["username"]
        self.password = test_config["password"]
        self.org_name = test_config["org_name"]
        self.space_name = test_config["space_name"]
        # TODO login to cfapi, setup requests session
        self.session = requests.Session()
        token_res = self.session.post(
            f"{self.uaa_url}/oauth/token",
            data={
                "client_id": "cf",
                "client_secret": "",
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
            },
        )
        token_res.raise_for_status()
        token = token_res.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        res = self.session.get(f"{self.cfapi_url}/v3/spaces?names={self.space_name}")
        res.raise_for_status()
        self.space_guid = res.json()["resources"][0]["guid"]


# global config shared by all ITs
itsconfig = ITsConfig()


class ShimTestCase(unittest.TestCase):
    config = itsconfig  # for setUpClass

    def __init__(self, methodname: str) -> None:
        super().__init__(methodname)
        self.config = itsconfig

    def run_v2_shim_get(self, endpoint: str) -> Tuple[Any, Any]:
        v2_res = self.config.session.get(f"{self.config.cfapi_url}{endpoint}")
        shim_res = self.config.session.get(f"{self.config.shim_url}{endpoint}")
        logger.debug(f"Testing {endpoint}: shim={shim_res.elapsed.total_seconds()} s, v2={v2_res.elapsed.total_seconds()} s")
        self.assertEqual(200, v2_res.status_code)
        self.assertEqual(200, shim_res.status_code)
        return v2_res.json(), shim_res.json()

    # a better way to compare dicts
    def assertDict(self, first: dict, second: dict):
        diff = DeepDiff(first, second, verbose_level=2)
        if len(diff) > 0:
            logger.error(pprint.pformat(diff))
        self.assertEqual(diff, {})
