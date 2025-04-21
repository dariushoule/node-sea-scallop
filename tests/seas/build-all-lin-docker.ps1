# docker image prune -a
Push-Location $PSScriptRoot
# docker build -t bullseye_slim_build:latest .
docker run --rm -v ${PWD}:/src -w /src bullseye_slim_build "./build-all-lin-docker.sh"
Pop-Location