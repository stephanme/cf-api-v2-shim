import logging

# configure logging before initializing further modules
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
# logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

import flask
import os
import json

vcap_application = json.loads(os.getenv("VCAP_APPLICATION", "{}"))

shim_url = vcap_application.get("application_uris", ["http://localhost:8080"])[0]
if not shim_url.startswith("http"):
    # application_uris are w/0 scheme
    shim_url = f"https://{shim_url}"
logger.info(f"shim_url: {shim_url}")

cfapi_url = ""
# assume that shim is deployed on CF landscape that shall be shimmed
cfapi_url = vcap_application.get("cf_api", cfapi_url)
cfapi_url = os.getenv("CFG_CF_API_URL", cfapi_url)
if not cfapi_url:
    raise ValueError("CFG_CF_API_URL not set")
logger.info(f"cfapi_url: {cfapi_url}")

proxy_v3 = os.getenv("CFG_PROXY_V3", "false") == "true"
logger.info(f"proxy_v3: {proxy_v3}")

app = flask.Flask(__name__)

# import modules with route definitions
import shim.root  # noqa: F401
import shim.apps  # noqa: F401
import shim.stacks  # noqa: F401


# TODO: graceful shutdown
port = int(os.getenv("PORT", 8080))
# don't expose for local testing
host = "127.0.0.1" if shim_url.startswith("http://localhost") else "0.0.0.0"
logger.info(f"Starting shim on {host}:{port}")
app.run(host=host, port=port)
