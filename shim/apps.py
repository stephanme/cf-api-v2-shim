import json
import flask
import requests
import logging
from __main__ import app, cfapi_url
from shim.utils import (
    cfapi_request_headers,
    cfapi_response_headers,
    filter_params_v2_to_v3,
    pagination_params_v2_to_v3,
    pagination_v3_to_v2,
)

logger = logging.getLogger(__name__)


def packackage_state_v3_to_v2(v3_package_state: str, v3_droplet_state: str) -> str:
    # TODO: v2 state = None possible? Test with app w/o package
    v3_state = v3_droplet_state if v3_droplet_state else v3_package_state
    if v3_state in ["FAILED", "EXPIRED"]:
        return "FAILED"
    elif v3_state == "STAGED":
        return "STAGED"
    else:
        return "PENDING"


def app_v3_to_v2(
    v3_app,
    v3_web_process,
    v3_latest_package,
    v3_latest_build,
    v3_droplet,
    v3_detected_system_buildpack,
    v3_stack,
    v3_app_env,
    v3_app_feature_ssh,
) -> dict:
    guid = v3_app["guid"]
    v3_lifecycle_type = v3_app["lifecycle"]["type"]
    v3_buildpack = (
        v3_app["lifecycle"]["data"]["buildpacks"][0]
        if v3_lifecycle_type == "buildpack" and v3_app["lifecycle"]["data"]["buildpacks"]
        else None
    )
    v3_latest_package_type = v3_latest_package["type"] if v3_latest_package else None
    v3_detected_buildpack = v3_droplet["buildpacks"][0] if v3_droplet and v3_droplet["buildpacks"] else None
    v3_error = v3_latest_build["error"] if v3_latest_build else v3_droplet["error"] if v3_droplet else None
    v2_staging_task_id = v3_latest_build["guid"] if v3_latest_build else v3_droplet["guid"] if v3_droplet else None
    v2_staging_failed = v3_error.split(" - ") if v3_error else [None, None]
    v2_package_state = packackage_state_v3_to_v2(
        v3_latest_package["state"] if v3_latest_package else None, v3_droplet["state"] if v3_droplet else None
    )

    v2_ports = [8080]
    if (
        v3_droplet
        and v3_droplet["lifecycle"]["type"] == "docker"
        and v3_droplet["execution_metadata"]
        # v3: execution_metadata is hidden in lists
        and v3_droplet["execution_metadata"][0] == "{"
    ):
        metadata = json.loads(v3_droplet["execution_metadata"])
        v2_ports = [p["Port"] for p in metadata["ports"]]

    return {
        "metadata": {
            "guid": guid,
            "url": f"/v2/apps/{guid}",
            "created_at": v3_web_process["created_at"],
            "updated_at": v3_web_process["updated_at"],
        },
        "entity": {
            "name": v3_app["name"],
            "production": False,
            "space_guid": v3_app["relationships"]["space"]["data"]["guid"],
            "stack_guid": v3_stack["guid"] if v3_stack else None,
            "buildpack": v3_buildpack,
            "detected_buildpack": v3_detected_buildpack["buildpack_name"] if v3_detected_buildpack else None,
            "detected_buildpack_guid": v3_detected_system_buildpack["guid"] if v3_detected_system_buildpack else None,
            "environment_json": v3_app_env["var"] if len(v3_app_env["var"]) > 0 else None,
            "memory": v3_web_process["memory_in_mb"],
            "instances": v3_web_process["instances"],
            "disk_quota": v3_web_process["disk_in_mb"],
            "log_rate_limit": v3_web_process["log_rate_limit_in_bytes_per_second"],
            "state": v3_app["state"],
            "version": v3_web_process["version"],
            "command": v3_web_process[
                "command"
            ],  # TODO: v2 = specified command, v3 = process.specified_or_detected_command, v3 bug? droplet contains detected command
            "console": False,
            "debug": None,
            "staging_task_id": v2_staging_task_id,
            "package_state": v2_package_state,
            "health_check_http_endpoint": v3_web_process["health_check"]["data"].get("endpoint"),
            "health_check_type": v3_web_process["health_check"]["type"],
            "health_check_timeout": v3_web_process["health_check"]["data"].get("timeout"),
            "staging_failed_reason": v2_staging_failed[0],
            "staging_failed_description": v2_staging_failed[1],
            "diego": True,
            "docker_image": v3_latest_package["data"]["image"] if v3_latest_package_type == "docker" else None,
            "docker_credentials": {
                "username": v3_latest_package["data"]["username"] if v3_latest_package_type == "docker" else None,
                "password": v3_latest_package["data"]["password"] if v3_latest_package_type == "docker" else None,
            },
            "package_updated_at": v3_latest_package["created_at"] if v3_latest_package else None,
            "detected_start_command": (
                v3_droplet["process_types"]["web"] if v3_droplet and "web" in v3_droplet["process_types"] else v3_web_process["command"]
            ),
            "enable_ssh": v3_app_feature_ssh["enabled"],
            "ports": v2_ports,
            "space_url": f"/v2/spaces/{v3_app['relationships']['space']['data']['guid']}",
            "stack_url": f"/v2/stacks/{v3_stack['guid']}" if v3_stack else None,
            "routes_url": f"/v2/apps/{guid}/routes",
            "events_url": f"/v2/apps/{guid}/events",
            "service_bindings_url": f"/v2/apps/{guid}/service_bindings",
            "route_mappings_url": f"/v2/apps/{guid}/route_mappings",
        },
    }


@app.route("/v2/apps/<uuid:guid>")
def v2_get_app(guid):
    # TODO: error handling after every request (e.g. exceptions, rate limits, not found etc)
    # TODO: requests could run in parallel
    with requests.Session() as session:
        session.headers.update(cfapi_request_headers(flask.request.headers))
        session.allow_redirects = False
        v3_app_res = session.get(f"{cfapi_url}/v3/apps/{guid}")
        v3_web_process_res = session.get(f"{cfapi_url}/v3/apps/{guid}/processes/web")
        v3_latest_package_res = session.get(f"{cfapi_url}/v3/apps/{guid}/packages?order_by=-created_at&per_page=1")
        v3_latest_build_res = session.get(f"{cfapi_url}/v3/apps/{guid}/builds?order_by=-created_at&per_page=1")
        v3_droplet_res = session.get(f"{cfapi_url}/v3/apps/{guid}/droplets/current")
        v3_app_env_res = session.get(f"{cfapi_url}/v3/apps/{guid}/environment_variables")
        v3_app_feature_ssh_res = session.get(f"{cfapi_url}/v3/apps/{guid}/features/ssh")

        v3_app = v3_app_res.json()
        v3_web_process = v3_web_process_res.json()

        v3_latest_package_json = v3_latest_package_res.json()
        v3_latest_package = (
            v3_latest_package_json["resources"][0]
            if v3_latest_package_res.status_code == 200 and v3_latest_package_json["pagination"]["total_results"] > 0
            else None
        )

        v3_latest_build_json = v3_latest_build_res.json()
        v3_latest_build = (
            v3_latest_build_json["resources"][0]
            if v3_latest_build_res.status_code == 200 and v3_latest_build_json["pagination"]["total_results"] > 0
            else None
        )

        v3_droplet = v3_droplet_res.json() if v3_droplet_res.status_code == 200 else None

        v3_app_env = v3_app_env_res.json()
        v3_app_feature_ssh = v3_app_feature_ssh_res.json()

        v3_stack = None
        v3_buildpack = None
        if v3_app["lifecycle"]["type"] == "buildpack":
            stack = v3_app["lifecycle"]["data"]["stack"]
            if stack:
                # TODO: cache stacks as they don't change
                v3_stack_res = session.get(f"{cfapi_url}/v3/stacks?names={stack}&per_page=1")
                v3_stack = v3_stack_res.json()["resources"][0] if v3_stack_res.status_code == 200 else None
            if v3_droplet:
                # take stack and buildpack from droplet (= detected buildpack)
                v3_buildpack_res = session.get(
                    f"{cfapi_url}/v3/buildpacks",
                    params={
                        "names": v3_droplet["buildpacks"][0]["name"],
                        "stacks": stack,
                        "per_page": 1,
                    },
                )
                v3_buildpack = (
                    v3_buildpack_res.json()["resources"][0]
                    if v3_buildpack_res.status_code == 200 and len(v3_buildpack_res.json()["resources"]) > 0
                    else None
                )
        elif v3_app["lifecycle"]["type"] == "docker":
            # for whatever reason, v2 reports the default stack for docker apps
            v3_stack_res = session.get(f"{cfapi_url}/v3/stacks?default=true&per_page=1")
            v3_stack = v3_stack_res.json()["resources"][0] if v3_stack_res.status_code == 200 else None

    v2_app = app_v3_to_v2(
        v3_app, v3_web_process, v3_latest_package, v3_latest_build, v3_droplet, v3_buildpack, v3_stack, v3_app_env, v3_app_feature_ssh
    )

    return flask.make_response(v2_app, v3_app_res.status_code, cfapi_response_headers(v3_app_res.headers))


# v2 apps endpoint is based on processes not apps - impacts sort order
@app.route("/v2/apps")
def v2_get_apps():
    with requests.Session() as session:
        session.headers.update(cfapi_request_headers(flask.request.headers))
        session.allow_redirects = False
        # Valid filters: name, space_guid, organization_guid, diego, stack_guid
        # TODO: q: diego, stack_guid
        params = {**pagination_params_v2_to_v3(flask.request.args), **filter_params_v2_to_v3(flask.request.args)}
        v3_apps_res = session.get(f"{cfapi_url}/v3/apps", params=params)
        v3_apps_json = v3_apps_res.json()
        v3_apps = {app["guid"]: app for app in v3_apps_json["resources"]}

        # TODO: could optimize for most filters and reuse apps filter (but not for name)
        # TODO: handle too many guids
        # TODO: list requests may need pagination
        query_params = {
            "app_guids": ",".join([guid for guid in v3_apps.keys()]),
            "per_page": 5000,
        }

        v3_web_processes_res = session.get(
            f"{cfapi_url}/v3/processes",
            params={
                **query_params,
                "types": "web",
            },
        )
        v3_web_processes = {
            process["relationships"]["app"]["data"]["guid"]: process for process in v3_web_processes_res.json()["resources"]
        }

        v3_packages_res = session.get(f"{cfapi_url}/v3/packages", params=query_params)
        v3_packages = {package["relationships"]["app"]["data"]["guid"]: package for package in v3_packages_res.json()["resources"]}

        v3_builds_res = session.get(f"{cfapi_url}/v3/builds?per_page=5000", params=query_params)
        v3_builds = {build["relationships"]["app"]["data"]["guid"]: build for build in v3_builds_res.json()["resources"]}

        # could improve when current_droplet is part of app relations
        v3_droplets_res = session.get(f"{cfapi_url}/v3/droplets", params=query_params)
        v3_droplets = {droplet["relationships"]["app"]["data"]["guid"]: droplet for droplet in v3_droplets_res.json()["resources"]}

        # TODO: stacks and system buildpacks could be cached
        v3_stacks_res = session.get(f"{cfapi_url}/v3/stacks")
        v3_stacks = {stack["name"]: stack for stack in v3_stacks_res.json()["resources"]}
        v3_default_stack = next((stack for stack in v3_stacks.values() if stack["default"]), None)
        v3_app_stacks = {
            # guid: v3_stacks.get(app["lifecycle"]["data"].get("stack") if app["lifecycle"]["data"].get("stack") else v3_default_stack)
            guid: v3_stacks.get(app["lifecycle"]["data"].get("stack")) if app["lifecycle"]["data"].get("stack") else v3_default_stack
            for (guid, app) in v3_apps.items()
        }
        v3_buildpacks_res = session.get(f"{cfapi_url}/v3/buildpacks")
        v3_buildpacks = {(buildpack["name"], buildpack["stack"]): buildpack for buildpack in v3_buildpacks_res.json()["resources"]}
        v3_app_buildpacks = {
            app_guid: v3_buildpacks.get((droplet["buildpacks"][0]["name"] if droplet["buildpacks"] else None, droplet["stack"]))
            for (app_guid, droplet) in v3_droplets.items()
        }

        # TODO: fetch env vars and ssh flag per app - should be improved in v3 to include in app response
        v3_app_env_vars = {}
        v3_app_feature_ssh = {}
        for guid in v3_apps.keys():
            env_vars = session.get(f"{cfapi_url}/v3/apps/{guid}/environment_variables").json()
            feature_ssh = session.get(f"{cfapi_url}/v3/apps/{guid}/features/ssh").json()
            v3_app_env_vars[guid] = env_vars
            v3_app_feature_ssh[guid] = feature_ssh

    v2_apps = {
        **pagination_v3_to_v2(v3_apps_json["pagination"], flask.request.args),
        "resources": [
            # v2 is based on processes not apps - impacts sort order
            app_v3_to_v2(
                v3_apps[guid],
                v3_proc,
                v3_packages.get(guid),
                v3_builds.get(guid),
                v3_droplets.get(guid),
                v3_app_buildpacks.get(guid),
                v3_app_stacks.get(guid),
                v3_app_env_vars.get(guid),
                v3_app_feature_ssh.get(guid),
            )
            for (guid, v3_proc) in v3_web_processes.items()
        ],
    }
    return flask.make_response(v2_apps, 200, cfapi_response_headers(v3_apps_res.headers))
