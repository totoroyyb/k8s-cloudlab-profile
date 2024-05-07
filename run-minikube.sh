#!/bin/bash

newgrp docker << EOF
minikube start >> /tmp/machine-setup-logs/minikube-start.log
EOF