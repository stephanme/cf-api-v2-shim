# setup a space with resources used in integration tests

set -ex

# read from config file
configjson=$(dirname "$0")/../testconfig.json

org=$(jq -r '.org_name' $configjson)
space=$(jq -r '.space_name' $configjson)
username=$(jq -r '.username' $configjson)

# assumes that user with OrgManager role is already logged in
cf t -o $org

# cleanup
cf delete-space -f  -o $org $space || true

# create space
cf create-space $space -o $org
cf set-space-role $username $org $space SpaceDeveloper
cf t -s $space

# create test apps

# app1 = unstaged app
cf create-app app1
# app2 = staged, detected system buildpack, no command, process health check, no env vars
cf push -f ./manifest-app2.yml
cf disable-ssh app2
cf stop app2 
# app3 = staged, custom buildpack, with command, http health check, with env vars
cf push -f ./manifest-app3.yml
cf enable-ssh app3
cf stop app3
# app4 = docker
cf push -f ./manifest-app4.yml
cf stop app4
