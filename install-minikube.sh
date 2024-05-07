#!/bin/bash

# install minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64

minikube config set driver docker
minikube delete
mkdir -p /tmp/machine-setup-logs/

newgrp docker
minikube start >> /tmp/machine-setup-logs/minikube-start.log
