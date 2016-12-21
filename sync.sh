#!/bin/bash

cd $(dirname $0)
gsutil rsync -c -r -d -x "sync\.sh|\.git" . gs://releases.rancher.com/install-docker
