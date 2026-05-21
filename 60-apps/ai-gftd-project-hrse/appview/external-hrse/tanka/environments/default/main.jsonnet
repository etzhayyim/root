// GFTD HRSE App - Tanka Version
local lib = import '../../../../../lib/main.libsonnet';

local config = {
  name: 'ai-gftd-hrse-app',
  image: 'registry.systems.gftd.dev/ai-gftd-performer-org-gftd-sys-app-hrse-pba7d22f@sha256:latest',
};

[
  lib.deployment.webDeployment(
    name=config.name,
    image=config.image,
    port=3000,
    replicas=1
  ),
  lib.service.httpService(
    name=config.name,
    port=80,
    targetPort=3000
  ),
]