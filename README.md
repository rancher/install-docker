# install-docker
Scripts for docker-machine to install a particular docker version

Hosted at https://releases.rancher.com/install-docker/x.y[.z].sh, e.g.: 

  - https://releases.rancher.com/install-docker/20.10.sh

Test bucket is located at https://releases.rancher.com/install-docker-dev/x.y[.z].sh

## Currently released versions

[![install-docker](https://img.shields.io/badge/dynamic/json?label=install-docker&query=%24.version&url=https%3A%2F%2Freleases.rancher.com%2Finstall-docker%2FVERSION)](https://github.com/rancher/install-docker/tags)
[![install-docker-dev](https://img.shields.io/badge/dynamic/json?label=install-docker-dev&query=%24.version&url=https%3A%2F%2Freleases.rancher.com%2Finstall-docker-dev%2FVERSION)](https://github.com/rancher/install-docker/commits/master)

## Add new docker release

Example adding 20.10.7 with diff from 20.10.6:

- Run `make add-new-version` with the previous and new version:
```
PREVIOUS_ADD_DOCKER_VERSION=20.10.6 ADD_DOCKER_VERSION=20.10.7 make add-new-version
```
- Generate distributed script by running `make generate`
- Under `dist/` create/update the proper docker install script symlink `<DOCKER_MAJOR>.<DOCKER_MINOR>.sh`, to the generated script. Ex: `ln -s 20.10.7.sh 20.10.sh`
- **Optional:** Run OS tests locally using `make test` (currently takes around 45 minutes)
- Commit changes and submit PR (this will start the tests as well)

## Test releases

The repo contains some tests to check if the docker install scripts are working fine on defined distros and versions. The tests are executed within a dind env for every `pkg/<DOCKER_VERSION>` folder, using the generated scripts to install and run docker on defined distros and versions.

`make test`

There is the default distros and versions definition to test:
```
TEST_OS_IMAGE_NAME=(ubuntu centos debian)
TEST_OS_IMAGE_TAG[0]="16.04 18.04 20.04"
TEST_OS_IMAGE_TAG[1]="centos7 centos8"
TEST_OS_IMAGE_TAG[2]="10"
```

The test definition can be overwritten on every docker version folder, using the shell script file `pkg/<DOCKER_VERSION>/config.sh`
```
#!/bin/sh

DOCKER_GIT_COMMIT="3d8fe77c2c46c5b7571f94b42793905e5b3e42e4"

TEST_OS_IMAGE_NAME=(ubuntu centos debian)
TEST_OS_IMAGE_TAG[0]="20.04"
TEST_OS_IMAGE_TAG[1]="centos7"
TEST_OS_IMAGE_TAG[2]="10"
```

**Tip** As dind test env doesn't use systemd, dockerd is started manually. The default timeout waiting until dockerd starts, is defined by env variable `DIND_TEST_WAIT=3s`. It can be overwritten on execution time if required, `DIND_TEST_WAIT=5s make test`

## Sync releases

On each merge to master, scripts in `dist/` will be uploaded to `install-docker-dev` bucket and can be retrieved using https://releases.rancher.com/install-docker-dev/$VERSION.sh. The commit of the version that was uploaded can be found on https://releases.rancher.com/install-docker-dev/VERSION

When testing has been completed, a tag can be created to upload the scripts in `dist/` to `install-docker` (https://releases.rancher.com/install-docker/$VERSION.sh). A tag consists of the latest Docker version in the repository (for example, `20.10.12`) and epoch timestamp (in case we need to release same set of versions with changes). The tag can be generated using `scripts/generate-release-tag`, or you can use the GitHub Actions workflow [Create release tag](https://github.com/rancher/install-docker/actions/workflows/create-tag.yml) directly. The tag of the version that was uploaded can be found on https://releases.rancher.com/install-docker/VERSION

## Previous manual instructions to add a new version

This script is based on public docker-install release, https://github.com/docker/docker-install . Docker-install script is built from the docker repo, and it's patched to generate a docker install script for a concrete docker version. The patch is also adding support for `oracle` and `rancheros` distros due to not supported on the original script.

To add a new docker installer version, follow these steps:
- Create a docker version folder under `pkg/<DOCKER_VERSION>`, version should follow [semver](https://semver.org/) format.  Ex: `pkg/20.10.2/`
- Under docker version folder: 
  - Download docker-install version from its repo `curl -Lsk http://get.docker.com/ -o <DOCKER_VERSION>.orig.sh` and make a copy `cp -p <DOCKER_VERSION>.orig.sh <DOCKER_VERSION>.sh`
  - Make all the needed changes at `<DOCKER_VERSION>.sh`. Don't remove `SCRIPT_COMMIT_SHA` var definition
  - Create diff file,  `diff -uNr <DOCKER_VERSION>.orig.sh <DOCKER_VERSION>.sh > pkg/<DOCKER_VERSION>/<DOCKER_VERSION>.diff` and remove . Ex: `pkg/20.10.2/20.10.2.diff`
```
 diff -uNr 20.10.2.orig.sh 20.10.2.sh
--- 20.10.2.orig.sh 2021-01-28 23:47:45.000000000 +0100
+++ 20.10.2.sh  2021-01-28 23:53:21.000000000 +0100
@@ -21,26 +21,11 @@
 # the script was uploaded (Should only be modified by upload job):
 SCRIPT_COMMIT_SHA="3d8fe77c2c46c5b7571f94b42793905e5b3e42e4"
 
-
-# The channel to install from:
-#   * nightly
-#   * test
-#   * stable
-#   * edge (deprecated)
-DEFAULT_CHANNEL_VALUE="stable"
-if [ -z "$CHANNEL" ]; then
- CHANNEL=$DEFAULT_CHANNEL_VALUE
-fi
-
-DEFAULT_DOWNLOAD_URL="https://download.docker.com"
-if [ -z "$DOWNLOAD_URL" ]; then
- DOWNLOAD_URL=$DEFAULT_DOWNLOAD_URL
-fi
-
-DEFAULT_REPO_FILE="docker-ce.repo"
-if [ -z "$REPO_FILE" ]; then
- REPO_FILE="$DEFAULT_REPO_FILE"
-fi
+CHANNEL="stable"
+DOWNLOAD_URL="https://download.docker.com"
+REPO_FILE="docker-ce.repo"
+VERSION=20.10.2
+DIND_TEST_WAIT=${DIND_TEST_WAIT:-3s}  # Wait time until docker start at dind test env
 
 mirror=''
 DRY_RUN=${DRY_RUN:-}
@@ -69,6 +54,18 @@
    ;;
 esac
 
+start_docker() {
+ if [ ! -z $DIND_TEST ]; then
+   # Starting dockerd manually due to dind env is not using systemd
+   dockerd &
+   sleep $DIND_TEST_WAIT
+ elif [ -d '/run/systemd/system' ] ; then
+   $sh_c 'systemctl start docker'
+ else
+   $sh_c 'service docker start'
+ fi
+}
+
 command_exists() {
  command -v "$@" > /dev/null 2>&1
 }
@@ -329,11 +326,20 @@
    ;;
 
    centos|rhel)
+     # installing centos packages
+     lsb_dist="centos"
      if [ -z "$dist_version" ] && [ -r /etc/os-release ]; then
        dist_version="$(. /etc/os-release && echo "$VERSION_ID")"
      fi
    ;;
 
+   oracleserver)
+     # installing centos packages
+     lsb_dist="centos"
+     # need to switch lsb_dist to match yum repo URL
+     dist_version="$(rpm -q --whatprovides redhat-release --queryformat "%{VERSION}\n" | sed 's/\/.*//' | sed 's/\..*//' | sed 's/Server*//')"
+   ;;
+
    *)
      if command_exists lsb_release; then
        dist_version="$(lsb_release --release | cut -f2)"
@@ -404,6 +410,7 @@
          $sh_c "apt-get install -y -qq --no-install-recommends docker-ce-cli=$cli_pkg_version >/dev/null"
        fi
        $sh_c "apt-get install -y -qq --no-install-recommends docker-ce$pkg_version >/dev/null"
+       start_docker
      )
      echo_docker_as_nonroot
      exit 0
@@ -474,10 +481,25 @@
          $sh_c "$pkg_manager install -y -q docker-ce-cli-$cli_pkg_version"
        fi
        $sh_c "$pkg_manager install -y -q docker-ce$pkg_version"
+       if ! command_exists iptables; then
+         $sh_c "$pkg_manager install -y -q iptables"
+       fi
+       start_docker
      )
      echo_docker_as_nonroot
      exit 0
      ;;
+   rancheros)
+     (
+     set -x
+     $sh_c "sleep 3;ros engine list --update"
+     engine_version="$(sudo ros engine list | awk '{print $2}' | grep ${docker_version} | tail -n 1)"
+     if [ "$engine_version" != "" ]; then
+       $sh_c "ros engine switch -f $engine_version"
+     fi
+     )
+     exit 0
+     ;;
    *)
      if [ -z "$lsb_dist" ]; then
        if is_darwin; then

```
  - Create shell script file `pkg/<DOCKER_VERSION>/config.sh`. To assure the patch would be applied to the same origin script version, this file should contain `DOCKER_GIT_COMMIT` var equal to `SCRIPT_COMMIT_SHA` got on first steps. Ex: [`pkg/20.10.2/config.sh`](pkg/20.10.2/config.sh)
```
#!/bin/sh

DOCKER_GIT_COMMIT="3d8fe77c2c46c5b7571f94b42793905e5b3e42e4"
```
  - Generate the docker version install script `dist/<DOCKER_VERSION>.sh` executing `make generate`. This command will generate docker version install script for every `pkg/<DOCKER_VERSION>` folder, if it doesn't exist and `pkg/<DOCKER_VERSION>/<DOCKER_VERSION>.diff` and `pkg/<DOCKER_VERSION>/config.sh` files exist. This command will also shows an info message for docker install scripts that were generated with older DOCKER_GIT_COMMIT, so they could be updated with latest released DOCKER_GIT_COMMIT. `git` and `curl` commands are required.
  Ex: Will generate [`dist/20.10.2.sh`](dist/20.10.2.sh).
  - Under `dist/` create/update the proper docker install script symlink `<DOCKER_MAJOR>.<DOCKER_MINOR>.sh`, to the generated script. Ex: `ln -s 20.10.2.sh 20.10.sh`
  - Define and execute tests, `make test`. See above for more info
  - Commit changes and submit PR 


