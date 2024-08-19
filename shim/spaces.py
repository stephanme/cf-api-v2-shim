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


def space_v3_to_v2(v3_space, v3_space_feature_ssh) -> dict:
    guid = v3_space["guid"]
    space_quota_guid = v3_space["relationships"]["quota"]["data"]["guid"] if v3_space["relationships"]["quota"]["data"] else None
    v2_space = {
        "entity": {
            "allow_ssh": v3_space_feature_ssh["enabled"],
            "app_events_url": f"/v2/spaces/{guid}/app_events",
            "apps_url": f"/v2/spaces/{guid}/apps",
            "auditors_url": f"/v2/spaces/{guid}/auditors",
            "developers_url": f"/v2/spaces/{guid}/developers",
            "domains_url": f"/v2/spaces/{guid}/domains",
            "events_url": f"/v2/spaces/{guid}/events",
            "isolation_segment_guid": None,  # TODO
            "managers_url": f"/v2/spaces/{guid}/managers",
            "name": v3_space["name"],
            "organization_guid": v3_space["relationships"]["organization"]["data"]["guid"],
            "organization_url": f"/v2/organizations/{v3_space['relationships']['organization']['data']['guid']}",
            "routes_url": f"/v2/spaces/{guid}/routes",
            "security_groups_url": f"/v2/spaces/{guid}/security_groups",
            "service_instances_url": f"/v2/spaces/{guid}/service_instances",
            "space_quota_definition_guid": space_quota_guid,
            "staging_security_groups_url": f"/v2/spaces/{guid}/staging_security_groups",
        },
        "metadata": {
            "guid": guid,
            "url": f"/v2/spaces/{guid}",
            "created_at": v3_space["created_at"],
            "updated_at": v3_space["updated_at"],
        },
    }
    return v2_space


@app.route("/v2/spaces/<uuid:guid>")
def v2_get_space(guid):
    with requests.Session() as session:
        session.headers.update(cfapi_request_headers(flask.request.headers))
        session.allow_redirects = False
        v3_space_res = session.get(f"{cfapi_url}/v3/spaces/{guid}")
        # TODO: v3_space_res.raise_for_status() + global error handling
        if v3_space_res.status_code >= 400:
            # TODO: error mapping
            return flask.make_response(v3_space_res.json(), v3_space_res.status_code, cfapi_response_headers(v3_space_res.headers))
        
        v3_space = v3_space_res.json()
        v3_space_feature_ssh_res = session.get(f"{cfapi_url}/v3/spaces/{guid}/features/ssh")
        v3_space_feature_ssh = v3_space_feature_ssh_res.json()

        v2_space = space_v3_to_v2(v3_space, v3_space_feature_ssh)
        return flask.make_response(v2_space, v3_space_res.status_code, cfapi_response_headers(v3_space_res.headers))

@app.route("/v2/spaces")
def v2_get_spaces():
    with requests.Session() as session:
        session.headers.update(cfapi_request_headers(flask.request.headers))
        session.allow_redirects = False
        # Valid filters: name, organization_guid, developer_guid, app_guid, isolation_segment_guid
        # order-by: id, name
        params = {**pagination_params_v2_to_v3(flask.request.args), **filter_params_v2_to_v3(flask.request.args)}

        space_guids = {}
        if "app_guids" in params:
            # translate v2 app_quid query to v3 apps query
            app_guids = params.pop("app_guids")
            v3_apps_res = session.get(f"{cfapi_url}/v3/apps", params={
                "guids": app_guids,
                "per_page": 5000,
            })
            v3_apps_res.raise_for_status()
            v3_apps = v3_apps_res.json()
            space_guids = {app["relationships"]["space"]["data"]["guid"] for app in v3_apps["resources"]}
        if "developer_guids" in params:
            # translate v2 developer_guid query to v3 roles query
            # TODO: won't work for users with many roles due to url length limit, alternative: roles query with include=space + local filtering of other q params
            # -> but breaks order_by and pagination
            developer_guids = params.pop("developer_guids")
            v3_roles_res = session.get(f"{cfapi_url}/v3/roles", params={
                "user_guids": developer_guids,
                "types": "space_auditor,space_developer,space_manager",
                "per_page": 5000,
            })
            v3_roles_res.raise_for_status()
            v3_roles = v3_roles_res.json()
            space_guids_roles = {role["relationships"]["space"]["data"]["guid"] for role in v3_roles["resources"] if role["relationships"]["space"]["data"]}
            # intersect with existing space_guids from app_guids query (q params are ANDed)
            if space_guids:
                space_guids = space_guids.intersection(space_guids_roles)
            else: 
                space_guids = space_guids_roles
        if space_guids:
            params["guids"] = ",".join(space_guids)

        v3_spaces_res = session.get(f"{cfapi_url}/v3/spaces", params=params)
        v3_spaces_json = v3_spaces_res.json()
        v3_spaces = {space["guid"]: space for space in v3_spaces_json["resources"]}

        v3_space_feature_ssh = {}
        for guid in v3_spaces.keys():
            feature_ssh = session.get(f"{cfapi_url}/v3/spaces/{guid}/features/ssh").json()
            v3_space_feature_ssh[guid] = feature_ssh

    v2_spaces = {
        **pagination_v3_to_v2(v3_spaces_json["pagination"], flask.request.args),
        "resources": [
            space_v3_to_v2(
                v3_space,
                v3_space_feature_ssh.get(guid),
            )
            for (guid, v3_space) in v3_spaces.items()
        ],
    }
    return flask.make_response(v2_spaces, 200, cfapi_response_headers(v3_spaces_res.headers))
