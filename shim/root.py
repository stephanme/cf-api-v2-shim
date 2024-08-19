import flask
import requests
import logging
from __main__ import app, cfapi_url, shim_url, proxy_v3
from shim.utils import cfapi_request_headers, cfapi_response_headers

logger = logging.getLogger(__name__)


@app.route("/")
def root():
    res = requests.get(
        url=f"{cfapi_url}/",
        headers=cfapi_request_headers(flask.request.headers),
        allow_redirects=False,
    )
    # TODO: error handling

    # adapt response
    # TODO: add v2 link for CF with disabled v2
    root_data = res.json()
    root_data["links"]["self"]["href"] = shim_url
    root_data["links"]["cloud_controller_v2"]["href"] = f"{shim_url}/v2"
    # no real need to proxy v3 but useful for testing
    if proxy_v3:
        root_data["links"]["cloud_controller_v3"]["href"] = f"{shim_url}/v3"

    return flask.make_response(root_data, res.status_code, cfapi_response_headers(res.headers))


@app.route("/v2/info")
def v2_info():
    with requests.Session() as session:
        session.headers.update(cfapi_request_headers(flask.request.headers))
        session.allow_redirects = False
        root_res = session.get(f"{cfapi_url}/")
        root_res.raise_for_status()
        v3_info_res = session.get(f"{cfapi_url}/v3/info")
        v3_info_res.raise_for_status()
        root = root_res.json()
        v3_info = v3_info_res.json()

    v2_info = {
        "name": v3_info["name"],
        "build": v3_info["build"],
        "support": "",  # TODO
        "version": v3_info["version"],
        "description": v3_info["description"],
        "authorization_endpoint": root["links"]["login"]["href"],
        "token_endpoint": root["links"]["uaa"]["href"],
        "min_cli_version": None if not v3_info["cli_version"]["minimum"] else v3_info["cli_version"]["minimum"],
        "min_recommended_cli_version": None if not v3_info["cli_version"]["recommended"] else v3_info["cli_version"]["recommended"],
        "app_ssh_endpoint": root["links"]["app_ssh"]["href"],
        "app_ssh_host_key_fingerprint": root["links"]["app_ssh"]["meta"]["host_key_fingerprint"],
        "app_ssh_oauth_client": root["links"]["app_ssh"]["meta"]["oauth_client"],
        "doppler_logging_endpoint": root["links"]["logging"]["href"],
        "api_version": root["links"]["cloud_controller_v2"]["meta"]["version"] if root["links"]["cloud_controller_v2"] else "2.237.0",  # TODO: define a v2 version for foundations with disabled/removed v2
        "osbapi_version": "2.15",  # TODO: missing in v3 info
        # "user": ""  TODO: user info not available in v3 info, could probably decode jwt token if available        
    }
    return flask.make_response(v2_info, v3_info_res.status_code, cfapi_response_headers(v3_info_res.headers))


@app.route("/v2", defaults={"path": ""})
@app.route("/v2/<path:path>")
def proxy_v2_unshimmed_requests(path):
    logger.warning(f"Forwarding unshimmed v2 request: {flask.request.url}")
    return forward_to_cfapi()


@app.route("/v3", defaults={"path": ""})
@app.route("/v3/<path:path>")
def proxy_v3_requests(path):
    if not proxy_v3:
        return flask.Response("Not Found", 404)
    return forward_to_cfapi()


def forward_to_cfapi():
    # ref. https://stackoverflow.com/a/36601467/248616
    res = requests.request(
        method=flask.request.method,
        url=flask.request.url.replace(flask.request.host_url, f"{cfapi_url}/"),
        headers=cfapi_request_headers(flask.request.headers),
        data=flask.request.get_data(),
        cookies=flask.request.cookies,
        allow_redirects=False,
    )
    # TODO: error handling

    response = flask.Response(res.content, res.status_code, cfapi_response_headers(res.headers))
    return response


@app.route("/health")
def health():
    return {"shim_url": shim_url, "cfapi_url": cfapi_url}
