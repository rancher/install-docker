#!/bin/bash

cd $(dirname $0)
gsutil rsync -c -r -d -x "sync\.sh|\.git|\.DS_Store" . gs://releases.rancher.com/install-docker
