#!/usr/bin/env node
/**
 * Seed initial vehicle data for kuruma.etzhayyim.com Phase 1.
 * Uses real-world specs for high-demand Japanese models.
 */

const API = 'https://kuruma.etzhayyim.com/xrpc/etzhayyim.kuruma.v1.KurumaCommandService/CreateVehicle';

const vehicles = [
  // Toyota
  { make: "Toyota", 'make_slug': "toyota", model: "Corolla", year: 2024, 'body_type': "sedan", engine: "1.8L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 140, torque: 185, 'weight_kg': 1375, 'length_mm': 4495, 'width_mm': 1790, 'height_mm': 1435, 'price_jpy': 2490000 },
  { make: "Toyota", 'make_slug': "toyota", model: "Corolla Touring", year: 2024, 'body_type': "wagon", engine: "1.8L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 140, torque: 185, 'weight_kg': 1400, 'length_mm': 4495, 'width_mm': 1790, 'height_mm': 1460, 'price_jpy': 2679000 },
  { make: "Toyota", 'make_slug': "toyota", model: "Prius", year: 2024, 'body_type': "hatchback", engine: "2.0L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 196, torque: 208, 'weight_kg': 1420, 'length_mm': 4600, 'width_mm': 1780, 'height_mm': 1430, 'price_jpy': 3200000 },
  { make: "Toyota", 'make_slug': "toyota", model: "Prius PHV", year: 2024, 'body_type': "hatchback", engine: "2.0L 4-cyl PHEV", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 223, torque: 208, 'weight_kg': 1570, 'length_mm': 4600, 'width_mm': 1780, 'height_mm': 1430, 'price_jpy': 4600000 },
  { make: "Toyota", 'make_slug': "toyota", model: "Alphard", year: 2024, 'body_type': "minivan", engine: "2.5L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "AWD", horsepower: 250, torque: 270, 'weight_kg': 2060, 'length_mm': 4995, 'width_mm': 1850, 'height_mm': 1935, 'price_jpy': 5400000 },
  { make: "Toyota", 'make_slug': "toyota", model: "Vellfire", year: 2024, 'body_type': "minivan", engine: "2.5L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "AWD", horsepower: 250, torque: 270, 'weight_kg': 2080, 'length_mm': 4995, 'width_mm': 1850, 'height_mm': 1945, 'price_jpy': 6550000 },
  { make: "Toyota", 'make_slug': "toyota", model: "Land Cruiser 300", year: 2024, 'body_type': "suv", engine: "3.3L V6 Diesel Twin-Turbo", transmission: "10AT", 'fuel_type': "diesel", 'drive_type': "AWD", horsepower: 309, torque: 700, 'weight_kg': 2550, 'length_mm': 4985, 'width_mm': 1990, 'height_mm': 1925, 'price_jpy': 7300000 },
  { make: "Toyota", 'make_slug': "toyota", model: "Land Cruiser 250", year: 2024, 'body_type': "suv", engine: "2.8L 4-cyl Diesel Turbo", transmission: "8AT", 'fuel_type': "diesel", 'drive_type': "AWD", horsepower: 204, torque: 500, 'weight_kg': 2240, 'length_mm': 4925, 'width_mm': 1980, 'height_mm': 1870, 'price_jpy': 5200000 },
  { make: "Toyota", 'make_slug': "toyota", model: "RAV4", year: 2024, 'body_type': "suv", engine: "2.5L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "AWD", horsepower: 222, torque: 239, 'weight_kg': 1690, 'length_mm': 4600, 'width_mm': 1855, 'height_mm': 1685, 'price_jpy': 3538000 },
  { make: "Toyota", 'make_slug': "toyota", model: "Harrier", year: 2024, 'body_type': "suv", engine: "2.5L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 218, torque: 221, 'weight_kg': 1620, 'length_mm': 4740, 'width_mm': 1855, 'height_mm': 1660, 'price_jpy': 3718000 },
  { make: "Toyota", 'make_slug': "toyota", model: "Yaris", year: 2024, 'body_type': "hatchback", engine: "1.5L 3-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 116, torque: 145, 'weight_kg': 1090, 'length_mm': 3950, 'width_mm': 1695, 'height_mm': 1500, 'price_jpy': 2013000 },
  { make: "Toyota", 'make_slug': "toyota", model: "Yaris Cross", year: 2024, 'body_type': "suv", engine: "1.5L 3-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "AWD", horsepower: 116, torque: 145, 'weight_kg': 1190, 'length_mm': 4180, 'width_mm': 1765, 'height_mm': 1590, 'price_jpy': 2284000 },
  { make: "Toyota", 'make_slug': "toyota", model: "Crown Crossover", year: 2024, 'body_type': "suv", engine: "2.5L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "AWD", horsepower: 234, torque: 270, 'weight_kg': 1770, 'length_mm': 4930, 'width_mm': 1840, 'height_mm': 1540, 'price_jpy': 4350000 },
  { make: "Toyota", 'make_slug': "toyota", model: "GR86", year: 2024, 'body_type': "coupe", engine: "2.4L Flat-4", transmission: "6MT", 'fuel_type': "gasoline", 'drive_type': "RWD", horsepower: 235, torque: 250, 'weight_kg': 1270, 'length_mm': 4265, 'width_mm': 1775, 'height_mm': 1310, 'price_jpy': 3036000 },
  { make: "Toyota", 'make_slug': "toyota", model: "GR Supra", year: 2024, 'body_type': "coupe", engine: "3.0L Inline-6 Turbo", transmission: "8AT", 'fuel_type': "gasoline", 'drive_type': "RWD", horsepower: 387, torque: 500, 'weight_kg': 1570, 'length_mm': 4380, 'width_mm': 1865, 'height_mm': 1290, 'price_jpy': 7313000 },
  { make: "Toyota", 'make_slug': "toyota", model: "Sienta", year: 2024, 'body_type': "minivan", engine: "1.5L 3-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 116, torque: 145, 'weight_kg': 1340, 'length_mm': 4260, 'width_mm': 1695, 'height_mm': 1695, 'price_jpy': 2380000 },
  // Honda
  { make: "Honda", 'make_slug': "honda", model: "Civic", year: 2024, 'body_type': "sedan", engine: "2.0L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 184, torque: 315, 'weight_kg': 1460, 'length_mm': 4550, 'width_mm': 1800, 'height_mm': 1415, 'price_jpy': 3940000 },
  { make: "Honda", 'make_slug': "honda", model: "Civic Type R", year: 2024, 'body_type': "hatchback", engine: "2.0L 4-cyl VTEC Turbo", transmission: "6MT", 'fuel_type': "gasoline", 'drive_type': "FWD", horsepower: 330, torque: 420, 'weight_kg': 1430, 'length_mm': 4595, 'width_mm': 1890, 'height_mm': 1405, 'price_jpy': 4997000 },
  { make: "Honda", 'make_slug': "honda", model: "N-BOX", year: 2024, 'body_type': "kei", engine: "0.66L 3-cyl Turbo", transmission: "CVT", 'fuel_type': "gasoline", 'drive_type': "FWD", horsepower: 64, torque: 104, 'weight_kg': 910, 'length_mm': 3395, 'width_mm': 1475, 'height_mm': 1790, 'price_jpy': 1649800 },
  { make: "Honda", 'make_slug': "honda", model: "Step WGN", year: 2024, 'body_type': "minivan", engine: "2.0L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 184, torque: 315, 'weight_kg': 1810, 'length_mm': 4830, 'width_mm': 1750, 'height_mm': 1845, 'price_jpy': 3382600 },
  { make: "Honda", 'make_slug': "honda", model: "Freed", year: 2024, 'body_type': "minivan", engine: "1.5L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 123, torque: 253, 'weight_kg': 1410, 'length_mm': 4310, 'width_mm': 1695, 'height_mm': 1755, 'price_jpy': 2850800 },
  { make: "Honda", 'make_slug': "honda", model: "Vezel", year: 2024, 'body_type': "suv", engine: "1.5L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 131, torque: 253, 'weight_kg': 1350, 'length_mm': 4330, 'width_mm': 1790, 'height_mm': 1580, 'price_jpy': 2658700 },
  { make: "Honda", 'make_slug': "honda", model: "ZR-V", year: 2024, 'body_type': "suv", engine: "2.0L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 184, torque: 315, 'weight_kg': 1560, 'length_mm': 4570, 'width_mm': 1840, 'height_mm': 1620, 'price_jpy': 3049700 },
  // Nissan
  { make: "Nissan", 'make_slug': "nissan", model: "Serena", year: 2024, 'body_type': "minivan", engine: "1.4L 3-cyl e-POWER", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 163, torque: 315, 'weight_kg': 1790, 'length_mm': 4690, 'width_mm': 1695, 'height_mm': 1870, 'price_jpy': 2768700 },
  { make: "Nissan", 'make_slug': "nissan", model: "Note", year: 2024, 'body_type': "hatchback", engine: "1.2L 3-cyl e-POWER", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 136, torque: 300, 'weight_kg': 1220, 'length_mm': 4045, 'width_mm': 1695, 'height_mm': 1520, 'price_jpy': 2299000 },
  { make: "Nissan", 'make_slug': "nissan", model: "X-Trail", year: 2024, 'body_type': "suv", engine: "1.5L 3-cyl VC-Turbo e-POWER", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "AWD", horsepower: 213, torque: 330, 'weight_kg': 1860, 'length_mm': 4660, 'width_mm': 1840, 'height_mm': 1720, 'price_jpy': 3510000 },
  { make: "Nissan", 'make_slug': "nissan", model: "Ariya", year: 2024, 'body_type': "suv", engine: "Dual Motor EV", transmission: "Direct", 'fuel_type': "electric", 'drive_type': "AWD", horsepower: 394, torque: 600, 'weight_kg': 2230, 'length_mm': 4595, 'width_mm': 1850, 'height_mm': 1665, 'price_jpy': 7408600 },
  { make: "Nissan", 'make_slug': "nissan", model: "Sakura", year: 2024, 'body_type': "kei", engine: "Single Motor EV", transmission: "Direct", 'fuel_type': "electric", 'drive_type': "FWD", horsepower: 64, torque: 195, 'weight_kg': 1080, 'length_mm': 3395, 'width_mm': 1475, 'height_mm': 1655, 'price_jpy': 2548700 },
  { make: "Nissan", 'make_slug': "nissan", model: "GT-R", year: 2024, 'body_type': "coupe", engine: "3.8L V6 Twin-Turbo", transmission: "6DCT", 'fuel_type': "gasoline", 'drive_type': "AWD", horsepower: 570, torque: 637, 'weight_kg': 1790, 'length_mm': 4710, 'width_mm': 1895, 'height_mm': 1370, 'price_jpy': 13768600 },
  // Mazda
  { make: "Mazda", 'make_slug': "mazda", model: "CX-5", year: 2024, 'body_type': "suv", engine: "2.5L 4-cyl", transmission: "6AT", 'fuel_type': "gasoline", 'drive_type': "AWD", horsepower: 190, torque: 252, 'weight_kg': 1610, 'length_mm': 4575, 'width_mm': 1845, 'height_mm': 1690, 'price_jpy': 2909500 },
  { make: "Mazda", 'make_slug': "mazda", model: "CX-60", year: 2024, 'body_type': "suv", engine: "3.3L Inline-6 Diesel Turbo", transmission: "8AT", 'fuel_type': "diesel", 'drive_type': "AWD", horsepower: 254, torque: 550, 'weight_kg': 1920, 'length_mm': 4740, 'width_mm': 1890, 'height_mm': 1685, 'price_jpy': 3234000 },
  { make: "Mazda", 'make_slug': "mazda", model: "MX-5 Miata", year: 2024, 'body_type': "convertible", engine: "1.5L 4-cyl", transmission: "6MT", 'fuel_type': "gasoline", 'drive_type': "RWD", horsepower: 132, torque: 152, 'weight_kg': 1010, 'length_mm': 3915, 'width_mm': 1735, 'height_mm': 1225, 'price_jpy': 2893000 },
  { make: "Mazda", 'make_slug': "mazda", model: "Mazda3", year: 2024, 'body_type': "sedan", engine: "2.0L 4-cyl e-SKYACTIV X", transmission: "6AT", 'fuel_type': "gasoline", 'drive_type': "FWD", horsepower: 190, torque: 240, 'weight_kg': 1410, 'length_mm': 4460, 'width_mm': 1795, 'height_mm': 1440, 'price_jpy': 2618000 },
  // Subaru
  { make: "Subaru", 'make_slug': "subaru", model: "Forester", year: 2024, 'body_type': "suv", engine: "2.0L Flat-4 Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "AWD", horsepower: 145, torque: 188, 'weight_kg': 1620, 'length_mm': 4640, 'width_mm': 1820, 'height_mm': 1730, 'price_jpy': 3069000 },
  { make: "Subaru", 'make_slug': "subaru", model: "Crosstrek", year: 2024, 'body_type': "suv", engine: "2.0L Flat-4 Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "AWD", horsepower: 145, torque: 188, 'weight_kg': 1540, 'length_mm': 4480, 'width_mm': 1800, 'height_mm': 1580, 'price_jpy': 2662000 },
  { make: "Subaru", 'make_slug': "subaru", model: "WRX S4", year: 2024, 'body_type': "sedan", engine: "2.4L Flat-4 Turbo", transmission: "CVT", 'fuel_type': "gasoline", 'drive_type': "AWD", horsepower: 275, torque: 375, 'weight_kg': 1590, 'length_mm': 4670, 'width_mm': 1825, 'height_mm': 1465, 'price_jpy': 4004000 },
  { make: "Subaru", 'make_slug': "subaru", model: "BRZ", year: 2024, 'body_type': "coupe", engine: "2.4L Flat-4", transmission: "6MT", 'fuel_type': "gasoline", 'drive_type': "RWD", horsepower: 235, torque: 250, 'weight_kg': 1270, 'length_mm': 4265, 'width_mm': 1775, 'height_mm': 1310, 'price_jpy': 3267000 },
  // Suzuki
  { make: "Suzuki", 'make_slug': "suzuki", model: "Jimny", year: 2024, 'body_type': "suv", engine: "0.66L 3-cyl Turbo", transmission: "5MT", 'fuel_type': "gasoline", 'drive_type': "AWD", horsepower: 64, torque: 96, 'weight_kg': 1040, 'length_mm': 3395, 'width_mm': 1475, 'height_mm': 1725, 'price_jpy': 1563000 },
  { make: "Suzuki", 'make_slug': "suzuki", model: "Swift", year: 2024, 'body_type': "hatchback", engine: "1.2L 3-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 82, torque: 108, 'weight_kg': 870, 'length_mm': 3860, 'width_mm': 1695, 'height_mm': 1500, 'price_jpy': 1727000 },
  { make: "Suzuki", 'make_slug': "suzuki", model: "Hustler", year: 2024, 'body_type': "kei", engine: "0.66L 3-cyl Turbo Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 64, torque: 98, 'weight_kg': 840, 'length_mm': 3395, 'width_mm': 1475, 'height_mm': 1680, 'price_jpy': 1365000 },
  // Daihatsu
  { make: "Daihatsu", 'make_slug': "daihatsu", model: "Tanto", year: 2024, 'body_type': "kei", engine: "0.66L 3-cyl", transmission: "CVT", 'fuel_type': "gasoline", 'drive_type': "FWD", horsepower: 52, torque: 60, 'weight_kg': 880, 'length_mm': 3395, 'width_mm': 1475, 'height_mm': 1755, 'price_jpy': 1353000 },
  { make: "Daihatsu", 'make_slug': "daihatsu", model: "Rocky", year: 2024, 'body_type': "suv", engine: "1.2L 3-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "FWD", horsepower: 106, torque: 170, 'weight_kg': 1070, 'length_mm': 3995, 'width_mm': 1695, 'height_mm': 1620, 'price_jpy': 2156500 },
  // Mitsubishi
  { make: "Mitsubishi", 'make_slug': "mitsubishi", model: "Outlander PHEV", year: 2024, 'body_type': "suv", engine: "2.4L 4-cyl PHEV", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "AWD", horsepower: 252, torque: 450, 'weight_kg': 2010, 'length_mm': 4710, 'width_mm': 1860, 'height_mm': 1745, 'price_jpy': 4842200 },
  { make: "Mitsubishi", 'make_slug': "mitsubishi", model: "Delica Mini", year: 2024, 'body_type': "kei", engine: "0.66L 3-cyl Turbo Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "AWD", horsepower: 64, torque: 100, 'weight_kg': 1000, 'length_mm': 3395, 'width_mm': 1475, 'height_mm': 1800, 'price_jpy': 1804000 },
  // Lexus
  { make: "Lexus", 'make_slug': "lexus", model: "NX 350h", year: 2024, 'body_type': "suv", engine: "2.5L 4-cyl Hybrid", transmission: "CVT", 'fuel_type': "hybrid", 'drive_type': "AWD", horsepower: 244, torque: 270, 'weight_kg': 1810, 'length_mm': 4660, 'width_mm': 1865, 'height_mm': 1660, 'price_jpy': 5200000 },
  { make: "Lexus", 'make_slug': "lexus", model: "RX 500h", year: 2024, 'body_type': "suv", engine: "2.4L 4-cyl Turbo Hybrid", transmission: "6AT", 'fuel_type': "hybrid", 'drive_type': "AWD", horsepower: 371, torque: 460, 'weight_kg': 2100, 'length_mm': 4890, 'width_mm': 1920, 'height_mm': 1700, 'price_jpy': 9000000 },
  { make: "Lexus", 'make_slug': "lexus", model: "IS 350", year: 2024, 'body_type': "sedan", engine: "3.5L V6", transmission: "8AT", 'fuel_type': "gasoline", 'drive_type': "RWD", horsepower: 311, torque: 380, 'weight_kg': 1640, 'length_mm': 4710, 'width_mm': 1840, 'height_mm': 1435, 'price_jpy': 6200000 },
];

async function createVehicle(v) {
  const res = await fetch(API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(v)
  });
  const data = await res.json();
  return { model: `${v.make} ${v.model}`, status: res.status, id: data.vehicle_id || data.error || 'unknown' };
}

async function main() {
  console.log(`Seeding ${vehicles.length} vehicles...`);
  const results = [];
  // Batch 5 at a time to avoid overwhelming the container
  for (let i = 0; i < vehicles.length; i += 5) {
    const batch = vehicles.slice(i, i + 5);
    const batchResults = await Promise.all(batch.map(createVehicle));
    results.push(...batchResults);
    console.log(`  [${i + batch.length}/${vehicles.length}] ${batchResults.map(r => `${r.model}: ${r.id}`).join(', ')}`);
  }
  const ok = results.filter(r => r.status === 200).length;
  console.log(`\nDone: ${ok}/${vehicles.length} vehicles created.`);
}

main().catch(console.error);
