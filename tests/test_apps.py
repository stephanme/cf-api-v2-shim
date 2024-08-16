import logging
from tests.shimtest import ShimTestCase

# import pprint

logger = logging.getLogger(__name__)


class AppsTest(ShimTestCase):
    @classmethod
    def setUpClass(cls):
        res = cls.config.session.get(
            f"{cls.config.cfapi_url}/v3/apps",
            params={
                "space_guids": cls.config.space_guid,
                "order_by": "name",
            },
        )
        res.raise_for_status()
        apps = res.json()["resources"]
        cls.app1_guid = apps[0]["guid"]
        cls.app2_guid = apps[1]["guid"]
        cls.app3_guid = apps[2]["guid"]
        cls.app4_guid = apps[3]["guid"]

    def test_v2_get_app_unstaged(self):
        endpoint = f"/v2/apps/{AppsTest.app1_guid}"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        # TODO: v2 = None, v3 = ""
        shim_json["entity"]["command"] = None
        self.assertDict(v2_json, shim_json)

    def test_v2_get_app_system_buildpack(self):
        endpoint = f"/v2/apps/{AppsTest.app2_guid}"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        # TODO: v2 = specified command, v3 = process.specified_or_detected_command, v3 bug? droplet contains detected command
        shim_json["entity"]["command"] = None
        self.assertDict(v2_json, shim_json)

    def test_v2_get_app_custom_buildpack_and_command(self):
        endpoint = f"/v2/apps/{AppsTest.app3_guid}"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, shim_json)

    def test_v2_get_app_docker(self):
        endpoint = f"/v2/apps/{AppsTest.app4_guid}"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        # see above
        shim_json["entity"]["command"] = None
        self.assertDict(v2_json, shim_json)

    def test_v2_get_apps(self):
        endpoint = f"/v2/apps?q=space_guid:{AppsTest.config.space_guid}"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        # logger.debug(f"v2[3]: {pprint.pformat(v2_json["resources"][3])}")
        # logger.debug(f"shim[3]: {pprint.pformat(shim_json["resources"][3])}")
        self.assertDict(v2_json, self.tweak_apps_shim_json(v2_json, shim_json))

    def test_v2_get_apps_q_name(self):
        endpoint = f"/v2/apps?q=name:app2&q=space_guid:{AppsTest.config.space_guid}"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        # see above
        shim_json["resources"][0]["entity"]["command"] = None
        # v3 hides detected_start_command in lists and returns [PRIVATE DATA HIDDEN IN LISTS], unclear why
        shim_json["resources"][0]["entity"]["detected_start_command"] = "$HOME/boot.sh"
        self.assertDict(v2_json, shim_json)

    def test_v2_get_apps_results_per_page(self):
        endpoint = f"/v2/apps?q=space_guid:{AppsTest.config.space_guid}&results-per-page=1"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, self.tweak_apps_shim_json(v2_json, shim_json))

        endpoint = f"/v2/apps?q=space_guid:{AppsTest.config.space_guid}&results-per-page=1&page=2"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, self.tweak_apps_shim_json(v2_json, shim_json))

        endpoint = f"/v2/apps?q=space_guid:{AppsTest.config.space_guid}&results-per-page=100&page=2"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        # v3 returns total_results=0 for too high page numbers
        shim_json["total_results"] = v2_json["total_results"]
        self.assertDict(v2_json, self.tweak_apps_shim_json(v2_json, shim_json))

        endpoint = f"/v2/apps?q=space_guid:{AppsTest.config.space_guid}&q=name:app2&results-per-page=1"
        (v2_json, shim_json) = self.run_v2_shim_get(endpoint)
        self.assertDict(v2_json, self.tweak_apps_shim_json(v2_json, shim_json))

    def tweak_apps_shim_json(self, v2_json, shim_json):
        for idx, app in enumerate(shim_json["resources"]):
            # TODO: v2 = specified command, v3 = process.specified_or_detected_command, v3 bug? droplet contains detected command
            app["entity"]["command"] = v2_json["resources"][idx]["entity"]["command"]
            # v3 hides detected_start_command in lists and returns [PRIVATE DATA HIDDEN IN LISTS], unclear why
            app["entity"]["detected_start_command"] = v2_json["resources"][idx]["entity"]["detected_start_command"]
            # v3 hides droplet.execution_metadata in lists and returns [PRIVATE DATA HIDDEN IN LISTS], unclear why
            app["entity"]["ports"] = v2_json["resources"][idx]["entity"]["ports"]
        return shim_json
