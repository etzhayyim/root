// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 etzhayyim Japan株式会社 / etzhayyim. All rights reserved.
// Licensed under the Apache License, Version 2.0 — see LICENSE at repo root.

// COFOG taxonomy skeleton (divisions + groups). Class entries are loaded
// separately from data/classes/*.json so we can implement them one-by-one
// (per cron iteration) without touching this file.
//
// Source: United Nations Statistics Division — COFOG (1999, last update 2014),
// public domain. https://unstats.un.org/unsd/classifications/Family/Detail/4
//
// Code packing: 4-digit class code = {division XX}{group Y}{class Z} → "XXYZ".
//   division code = class.slice(0, 2)
//   group code    = class.slice(0, 3)

export const APP_DID = "did:web:open-cofog.etzhayyim.com";

export interface Division { code: string; nameEn: string; }
export interface Group    { code: string; nameEn: string; division: string; }
export interface CofogClass {
  code: string;
  nameEn: string;
  group: string;
  description?: string;
  includes?: string[];
  excludes?: string[];
  implementedAt?: string;
}

export const DIVISIONS: Division[] = [
  { code: "01", nameEn: "General public services" },
  { code: "02", nameEn: "Defence" },
  { code: "03", nameEn: "Public order and safety" },
  { code: "04", nameEn: "Economic affairs" },
  { code: "05", nameEn: "Environmental protection" },
  { code: "06", nameEn: "Housing and community amenities" },
  { code: "07", nameEn: "Health" },
  { code: "08", nameEn: "Recreation, culture and religion" },
  { code: "09", nameEn: "Education" },
  { code: "10", nameEn: "Social protection" },
];

// Groups are derived from the 96-class coverage in this monorepo
// (matches etzhayyim-project-cofog/appview/* per-class actors).
export const GROUPS: Group[] = [
  // 01 General public services
  { code: "011", nameEn: "Executive and legislative organs, financial and fiscal affairs, external affairs", division: "01" },
  { code: "012", nameEn: "Foreign economic aid", division: "01" },
  { code: "013", nameEn: "General services", division: "01" },
  { code: "014", nameEn: "Public debt transactions", division: "01" },
  { code: "015", nameEn: "Transfers of a general character between different levels of government", division: "01" },

  // 02 Defence
  { code: "021", nameEn: "Military defence", division: "02" },
  { code: "022", nameEn: "Civil defence", division: "02" },
  { code: "023", nameEn: "Foreign military aid", division: "02" },
  { code: "024", nameEn: "R&D Defence", division: "02" },
  { code: "025", nameEn: "Defence n.e.c.", division: "02" },

  // 03 Public order and safety
  { code: "031", nameEn: "Police services", division: "03" },
  { code: "032", nameEn: "Fire-protection services", division: "03" },
  { code: "033", nameEn: "Law courts", division: "03" },
  { code: "034", nameEn: "Prisons", division: "03" },
  { code: "035", nameEn: "R&D Public order and safety", division: "03" },
  { code: "036", nameEn: "Public order and safety n.e.c.", division: "03" },

  // 04 Economic affairs
  { code: "041", nameEn: "General economic, commercial and labour affairs", division: "04" },
  { code: "042", nameEn: "Agriculture, forestry, fishing and hunting", division: "04" },
  { code: "043", nameEn: "Fuel and energy", division: "04" },
  { code: "044", nameEn: "Mining, manufacturing and construction", division: "04" },
  { code: "045", nameEn: "Transport", division: "04" },
  { code: "046", nameEn: "Communication", division: "04" },
  { code: "047", nameEn: "Other industries", division: "04" },
  { code: "048", nameEn: "R&D Economic affairs", division: "04" },
  { code: "049", nameEn: "Economic affairs n.e.c.", division: "04" },

  // 05 Environmental protection
  { code: "051", nameEn: "Waste management", division: "05" },
  { code: "052", nameEn: "Waste water management", division: "05" },
  { code: "053", nameEn: "Pollution abatement", division: "05" },
  { code: "054", nameEn: "Protection of biodiversity and landscape", division: "05" },
  { code: "055", nameEn: "R&D Environmental protection", division: "05" },
  { code: "056", nameEn: "Environmental protection n.e.c.", division: "05" },

  // 06 Housing and community amenities
  { code: "061", nameEn: "Housing development", division: "06" },
  { code: "062", nameEn: "Community development", division: "06" },
  { code: "063", nameEn: "Water supply", division: "06" },
  { code: "064", nameEn: "Street lighting", division: "06" },
  { code: "065", nameEn: "R&D Housing and community amenities", division: "06" },
  { code: "066", nameEn: "Housing and community amenities n.e.c.", division: "06" },

  // 07 Health
  { code: "071", nameEn: "Medical products, appliances and equipment", division: "07" },
  { code: "072", nameEn: "Outpatient services", division: "07" },
  { code: "073", nameEn: "Hospital services", division: "07" },
  { code: "074", nameEn: "Public health services", division: "07" },
  { code: "075", nameEn: "R&D Health", division: "07" },
  { code: "076", nameEn: "Health n.e.c.", division: "07" },

  // 08 Recreation, culture and religion
  { code: "081", nameEn: "Recreational and sporting services", division: "08" },
  { code: "082", nameEn: "Cultural services", division: "08" },
  { code: "083", nameEn: "Broadcasting and publishing services", division: "08" },
  { code: "084", nameEn: "Religious and other community services", division: "08" },
  { code: "085", nameEn: "R&D Recreation, culture and religion", division: "08" },
  { code: "086", nameEn: "Recreation, culture and religion n.e.c.", division: "08" },

  // 09 Education
  { code: "091", nameEn: "Pre-primary and primary education", division: "09" },
  { code: "092", nameEn: "Secondary education", division: "09" },
  { code: "093", nameEn: "Post-secondary non-tertiary education", division: "09" },
  { code: "094", nameEn: "Tertiary education", division: "09" },
  { code: "095", nameEn: "Education not definable by level", division: "09" },
  { code: "096", nameEn: "Subsidiary services to education", division: "09" },
  { code: "097", nameEn: "R&D Education", division: "09" },
  { code: "098", nameEn: "Education n.e.c.", division: "09" },

  // 10 Social protection
  { code: "101", nameEn: "Sickness and disability", division: "10" },
  { code: "102", nameEn: "Old age", division: "10" },
  { code: "103", nameEn: "Survivors", division: "10" },
  { code: "104", nameEn: "Family and children", division: "10" },
  { code: "105", nameEn: "Unemployment", division: "10" },
  { code: "106", nameEn: "Housing", division: "10" },
  { code: "107", nameEn: "Social exclusion n.e.c.", division: "10" },
  { code: "108", nameEn: "R&D Social protection", division: "10" },
  { code: "109", nameEn: "Social protection n.e.c.", division: "10" },
];

export function didForDivision(code: string) { return `${APP_DID}:division:${code}`; }
export function didForGroup(code: string)    { return `${APP_DID}:group:${code}`; }
export function didForClass(code: string)    { return `${APP_DID}:class:${code}`; }

export function divisionOf(groupCode: string): string { return groupCode.slice(0, 2); }
export function groupOf(classCode: string): string    { return classCode.slice(0, 3); }
