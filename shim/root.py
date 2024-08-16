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
    return forward_to_cfapi()


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
