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


def stack_v3_to_v2(v3_stack):
    return {
        "metadata": {
            "guid": v3_stack["guid"],
            "url": f"/v2/stacks/{v3_stack['guid']}",
            "created_at": v3_stack["created_at"],
            "updated_at": v3_stack["updated_at"],
        },
        "entity": {
            "name": v3_stack["name"],
            "description": v3_stack["description"],
            "build_rootfs_image": v3_stack["build_rootfs_image"],
            "run_rootfs_image": v3_stack["run_rootfs_image"],
        },
    }


@app.route("/v2/stacks/<uuid:guid>")
def v2_get_stack(guid):
    with requests.Session() as session:
        session.headers.update(cfapi_request_headers(flask.request.headers))
        session.allow_redirects = False
        v3_stack_res = session.get(url=f"{cfapi_url}/v3/stacks/{guid}")
        v3_stack = v3_stack_res.json()

    return flask.make_response(stack_v3_to_v2(v3_stack), 200, cfapi_response_headers(v3_stack_res.headers))


# TODO inline-relations-depth - should not exist for this endpoint
@app.route("/v2/stacks")
def v2_get_stacks():
    with requests.Session() as session:
        session.headers.update(cfapi_request_headers(flask.request.headers))
        session.allow_redirects = False
        params = {**pagination_params_v2_to_v3(flask.request.args), **filter_params_v2_to_v3(flask.request.args)}
        v3_stacks_res = session.get(url=f"{cfapi_url}/v3/stacks", params=params)
        v3_stacks = v3_stacks_res.json()

    v2_stacks = {
        **pagination_v3_to_v2(v3_stacks["pagination"], flask.request.args),
        "resources": [stack_v3_to_v2(v3_stack) for v3_stack in v3_stacks["resources"]],
    }
    return flask.make_response(v2_stacks, 200, cfapi_response_headers(v3_stacks_res.headers))
