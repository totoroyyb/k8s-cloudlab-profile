#!/bin/bash

set -x
# install minikube
curl -L -o /tmp/minikube-linux-amd64 https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
pushd /tmp
sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64
popd

minikube config set driver docker
minikube delete
mkdir -p /tmp/machine-setup-logs/

# sudo -u $USER /local/repository/run-minikube.sh
set +x
