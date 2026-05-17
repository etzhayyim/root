#!/bin/bash
export MURAKUMO_API_KEY="local-test-key"
export MURAKUMO_API_URL="http://127.0.0.1:8888/v1"
export MURAKUMO_VK_NODE_NAME="murakumo-mac-node"
export KUBECONFIG=~/.kube/config
./murakumo-kubelet
