# POC: CF API v2 Shim

This POC shall find out how difficult it is to implement [CF API v2](https://v2-apidocs.cloudfoundry.org/) by translating the requests to [CF API v3](https://v3-apidocs.cloudfoundry.org/). Background is that CF API v2 is deprecated since very long time and [[RFC] CF API v2 End of Life](https://github.com/cloudfoundry/community/pull/941) proposes a roadmap for its removal.

Even a partial implementation might help for specific use cases and help v2 users to spread their v3 migration efforts over time.

Basic idea is to implement the shim as stateless application that can be deployed on the CF foundation to be shimmed. This decouples the shim from the CF deployment itself and allows CF users to deploy, fork, modify the shim according to their needs without depending on CF operators or the CF community (like waiting for new cf-deployment releases).

## Implemented v2 endpoints

- (root)
- `GET /v2/apps`
- `GET /v2/apps/:guid`
- `GET /v2/info`
- `GET /v2/spaces`
- `GET /v2/spaces/:guid`
- `GET /v2/stacks`
- `GET /v2/stacks/:guid`

All v2 endpoints that are not yet shimmed are simply forwarded as-is to the underlying CF API.

## Specific Challenges to be demonstrated by the POC

- [x] translation of a simple GET (`/v2/stacks/:guid`)
- [x] translation of a complex GET (`/v2/apps/:guid`)
- [x] list endpoints with pagination and sorting (`/v2/apps`)
- [x] list endpoints with non-matching query parameters (`/v2/spaces?q=app_guid|developer_guid`)
- [ ] summary endpoint
- [ ] modifying endpoints (POST, PATCH, DELETE)
- [ ] asynchronous endpoint
- [ ] synchronous v2 endpoint (`async` parameter) that is always async in v3
  - needs polling in shim
  - jwt token may expire
- [ ] `recursive` parameter for certain DELETE operations
- [x] vcap-request-id, tracing and rate limiting headers
  - request headers of v2 call are used for all v3 requests
  - currently the response headers of the 'main' v3 request are returned (without "hop-by-hop" headers)
- [ ] consistent error handling
  - exceptions when calling CF API
  - error aggregation when multiple v3 requests are involved
  - provide std CF API error responses for errors in shim
- [ ] url length restrictions on query params (translation of v2 to v3 may lead to very long guid lists)

## Out of Scope

- This is a POC and not a production-ready, well-tested implementation.
  - there are some integration tests that compare the shim response with the reponse of the real CF API v2 (assumption: v2 is still available on the CF foundation)
  - Flask dev server is used, doesn't support keep-alive
- Shimming the complete CF API v2 (see above for implemented endpoints).
- 100% perfect shimming of implemented endpoints
  - 90% running is better than 100% not running ;-)
  - see tests for known differences between v2 and shim
- Performance
  - most v2 requests map to multiple v3 requests
  - many of the v3 requests could run in parallel e.g. using async requests and web server implementation in Python
  - consider golang/Java/Rust etc for better performance and multi-threading support (but Python with async libs should be good enough)
- `inline-relations-depth` parameters in v2
  - [deprecated](https://v2-apidocs.cloudfoundry.org/apps/list_all_apps.html) already within v2 (i.e. double deprecated), at least since 2016 when the v2 docs moved to [cloud_controller_ng](https://github.com/cloudfoundry/cloud_controller_ng/commit/758323f9370dc5afb4e1919e4e4e13613395cbb9#diff-603027238c16955117ee965bc6703e0a46366d67b5ea477929e78659e8627c54R170) (not sure where to find the mentioned API specs)
  - implementation is probably possible but extra complex and slow

## Findings

List of interesting observations like inconsistencies or ideas for improving v3:

- v3 `process.command` shows specifed or detected command (in constrast to v3 doc). Bug? Detected command is available in droplet.
- certain info like droplet.process_type hash and droplet.execution_metadata are redacted from v3 list endpoints. Why? User can get the info via "by id" endpoint anyway.
- v3: 100 builds per app (`cc.max_retained_builds_per_app`). Makes e.g. `/v2/apps` endpoint slower than necessary. An additional `max_builds_per_app` query parameter for `/v3/builds` could help.
- apps sort order: v2 by process id; v3 by app id
- v3: order_by=id is not possible but it is the default sort order -> not possible to have initial sort order descending (workaround: `-created_at`)
- v3 pagination: total_results = 0 if page is too high (should return correct total results)
- v3: `GET /v3/apps` should allow to include env_vars and app feature flags. Similar for space feature flags.

## Development

Prerequisites
- Python 3.12 (virtual) environment
- CF foundation with enabled v2 and Org Manager rights in an org
- recommended: VS Code

### Local Dev

```
# install dependencies
pip install -f requirements.txt -U

# run shim
export CFG_CF_API_URL=<CF API root URL>
export CFG_PROXY_V3=<true|false>
python -m shim

# test that shim works
cf api http://localhost:8080
cf login

cf curl / -v               # root endpoint, check that v2 endpoint refers to shim
cf curl /v2/stacks -v      # a shimmed v2 request, translated into v3 requests by shim
cf curl /v2/buildpacks -v  # v2 request not yet implemented, forwarded to CF API as-is 
cf curl /v3/stacks -v      # proxied v3 request if CFG_PROXY_V3=true
```

Running tests
```
# install dependencies
pip install -f requirements-dev.txt -U

# linting
python -m flake8

# integration test setup
# copy testconfig.template to testconfig.json and adapt to you setup

# create test resources in a space, login as Org Manager for the org specified in testconfig.json
cf login
./tests/resources/setup.sh

# run tests, assumes a running shim (see above)
python -m unittest discover -s ./tests
```

### Deploy as CF app

```
# login as Space Developer and target a space (not the cfapiv2shimtest space used for testing)
cf login

# adapt manifest.yml if needed
cf push

# check that shim works
cf api https://cfapiv2shim.<domain>
cf login

cf curl / -v               # root endpoint, check that v2 endpoint refers to shim
cf curl /v2/stacks -v      # a shimmed v2 request, translated into v3 requests by shim
```
