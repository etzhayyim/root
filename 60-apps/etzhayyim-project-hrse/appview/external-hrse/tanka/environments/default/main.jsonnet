// Etzhayyim HRSE App - Tanka Version
local lib = import '../../../../../lib/main.libsonnet';

local config = {
  name: 'etzhayyim-hrse-app',
  image: 'registry.systems.etzhayyim.dev/etzhayyim-performer-org-etzhayyim-sys-app-hrse-pba7d22f@sha256:latest',
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