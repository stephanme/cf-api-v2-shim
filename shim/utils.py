import logging
import urllib
from werkzeug.datastructures import MultiDict

logger = logging.getLogger(__name__)


def cfapi_request_headers(headers: dict) -> dict:
    return {k: v for k, v in headers if k.lower() != "host"}  # exclude 'host' header


def cfapi_response_headers(headers: dict) -> dict:
    # v2 has no x-runtime header
    # TODO: exclude all "hop-by-hop headers" defined by RFC 2616 section 13.5.1 ref. https://www.rfc-editor.org/rfc/rfc2616#section-13.5.1
    excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection", "keep-alive", "date", "x-runtime"]
    return {k: v for k, v in headers.items() if k.lower() not in excluded_headers}


def pagination_url_v3_to_v2(url: str, v2_params: MultiDict) -> str:
    v3_parsed_url = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(v3_parsed_url.query)
    
    order_dir = "asc"
    order_by = ""
    if "order_by" in qs:
        order_by = qs.get("order_by")[0]
        if order_by.startswith("-"):
            order_dir = "desc"
            order_by = order_by[1:]
        if order_by.startswith("+"):
            order_by = order_by[1:]
        # v2: order-direction=desc -> v3: order_by=-created_at -> no v2 order-by param
        if order_by == "created_at":
            order_by = ""
    # v3 doesn't know order_by id
    if v2_params.get("order-by", "") == "id":
        order_by = "id"

    page = qs["page"][0]
    per_page = qs["per_page"][0]
    q = ""
    for q_param in v2_params.getlist("q"):
        q += f"&q={q_param}"

    if order_by:
        v2_url = f"{v3_parsed_url.path}?order-by={order_by}&order-direction={order_dir}&page={page}{q}&results-per-page={per_page}"
    else:
        v2_url = f"{v3_parsed_url.path}?order-direction={order_dir}&page={page}{q}&results-per-page={per_page}"

    return f"/v2{v2_url[3:]}"


def pagination_v3_to_v2(v3_pagination: dict, v2_params: MultiDict) -> dict:
    return {
        "total_results": v3_pagination["total_results"],
        "total_pages": v3_pagination["total_pages"],
        "prev_url": pagination_url_v3_to_v2(v3_pagination["previous"]["href"], v2_params) if v3_pagination["previous"] else None,
        "next_url": pagination_url_v3_to_v2(v3_pagination["next"]["href"], v2_params) if v3_pagination["next"] else None,
    }


def pagination_params_v2_to_v3(v2_params: MultiDict) -> dict:
    v3_params = {}
    if "results-per-page" in v2_params:
        v3_params["per_page"] = v2_params["results-per-page"]
    if "page" in v2_params:
        v3_params["page"] = v2_params["page"]
    order_by = v2_params.get("order-by", "id")
    order_by = "" if order_by == "id" else order_by
    order_by = "-" + order_by if "order-direction" in v2_params and v2_params["order-direction"] == "desc" else order_by
    order_by = "-created_at" if order_by == "-" else order_by
    if order_by:
        v3_params["order_by"] = order_by
    return v3_params


# TODO: pass valid filter params
def filter_params_v2_to_v3(v2_params: MultiDict) -> dict:
    # logger.debug(f"v2_params: {v2_params}")
    v3_params = {}  # MultiDict?
    for f in v2_params.getlist("q"):
        (key, value) = query_filter_v2_to_v3(f)
        v3_params[key] = value
    return v3_params


# lib/vcap/rest_api/query.rb
def query_filter_v2_to_v3(filter: str) -> tuple[str, str]:
    # logger.debug(f"filter: {filter}")
    split = filter.split(":", 1)
    if len(split) == 2:
        return (split[0] + "s", split[1])

    split = filter.split(" IN ", 1)
    if len(split) == 2:
        return (split[0] + "s", split[1])

    split = filter.split(">=", 1)
    if len(split) == 2:
        return (split[0] + "s[gte]", split[1])

    split = filter.split("<=", 1)
    if len(split) == 2:
        return (split[0] + "s[lte]", split[1])

    split = filter.split(">", 1)
    if len(split) == 2:
        return (split[0] + "s[gt]", split[1])

    split = filter.split("<", 1)
    if len(split) == 2:
        return (split[0] + "s[lt]", split[1])

    raise ValueError(f"Invalid filter: {filter}")  # TODO: api compliant error (4xx with error message)
