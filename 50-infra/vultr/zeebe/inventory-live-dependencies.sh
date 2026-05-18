#!/usr/bin/env bash
set -euo pipefail

echo "== Zeebe/pyzeebe images =="
kubectl get deploy,statefulset,cronjob -A \
  -o jsonpath='{range .items[?(@.spec.template.spec.containers)]}{.kind}{"\t"}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{range .spec.template.spec.containers[*]}{.image}{" "}{end}{"\n"}{end}' \
  | grep -Ei 'zeebe|pyzeebe' \
  | sort || true

echo
echo "== ZEEBE_GATEWAY consumers =="
kubectl get deploy,cronjob -A \
  -o go-template='{{range .items}}{{ $kind := .kind }}{{ $ns := .metadata.namespace }}{{ $name := .metadata.name }}{{range .spec.template.spec.containers}}{{ $cname := .name }}{{range .env}}{{if eq .name "ZEEBE_GATEWAY"}}{{printf "%s\t%s\t%s\t%s\t%s\n" $kind $ns $name $cname .value}}{{end}}{{end}}{{end}}{{end}}' \
  | sort || true

echo
echo "== Worker profiles =="
kubectl get deploy,cronjob -A \
  -o go-template='{{range .items}}{{ $kind := .kind }}{{ $ns := .metadata.namespace }}{{ $name := .metadata.name }}{{range .spec.template.spec.containers}}{{ $cname := .name }}{{range .env}}{{if eq .name "ZEEBE_WORKER_PROFILE"}}{{printf "%s\t%s\t%s\t%s\t%s\n" $kind $ns $name $cname .value}}{{end}}{{end}}{{end}}{{end}}' \
  | sort || true

echo
echo "== Spiff replacements already live =="
kubectl get deploy -A \
  -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{range .spec.template.spec.containers[*]}{.image}{" "}{end}{"\n"}{end}' \
  | grep -Ei 'spiff|bpmn-engine-host' \
  | sort || true

echo
echo "== LangGraph runtime =="
kubectl -n mitama-udf get deploy langgraph-server -o wide || true
