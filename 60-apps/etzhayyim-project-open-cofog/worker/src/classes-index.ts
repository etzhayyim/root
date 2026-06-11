// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 etzhayyim Japan株式会社 / etzhayyim. All rights reserved.
// Licensed under the Apache License, Version 2.0 — see LICENSE at repo root.

// Generated incrementally as data/classes/*.json files are added.
// As each new class JSON is added under data/classes/, append one import
// line + one CLASSES entry here, then bump IMPLEMENTED_COUNT.
//
// Progress: 10 / 96 COFOG classes implemented (one per division as seed).
// Cron `*/10 * * * *` (loop session) fills the rest one-by-one.

import c0111 from "../../data/classes/0111.json";
import c0210 from "../../data/classes/0210.json";
import c0310 from "../../data/classes/0310.json";
import c0411 from "../../data/classes/0411.json";
import c0510 from "../../data/classes/0510.json";
import c0610 from "../../data/classes/0610.json";
import c0711 from "../../data/classes/0711.json";
import c0810 from "../../data/classes/0810.json";
import c0911 from "../../data/classes/0911.json";
import c1011 from "../../data/classes/1011.json";

import type { CofogClass } from "./taxonomy";

export const CLASSES: Record<string, CofogClass> = {
  "0111": c0111 as CofogClass,
  "0210": c0210 as CofogClass,
  "0310": c0310 as CofogClass,
  "0411": c0411 as CofogClass,
  "0510": c0510 as CofogClass,
  "0610": c0610 as CofogClass,
  "0711": c0711 as CofogClass,
  "0810": c0810 as CofogClass,
  "0911": c0911 as CofogClass,
  "1011": c1011 as CofogClass,
};

export const IMPLEMENTED_COUNT = Object.keys(CLASSES).length;
export const TOTAL_CLASSES = 96; // etzhayyim-project-cofog actor count
