const endpoint = process.env.CACHE_PURGE_ENDPOINT || 'https://yoro.etzhayyim.com/api/internal/cache/purge';
const apiKey = process.env.CACHE_PURGE_API_KEY || '';

const defaultFiles = [
  'https://yoro.etzhayyim.com/',
  'https://yoro.etzhayyim.com/vibes',
  'https://yoro.etzhayyim.com/search',
];

const files = process.argv.slice(2);
const payload = { files: files.length > 0 ? files : defaultFiles };

const headers = {
  'Content-Type': 'application/json',
};
if (apiKey.trim()) {
  headers.Authorization = `Bearer ${apiKey.trim()}`;
}

const res = await fetch(endpoint, {
  method: 'POST',
  headers,
  body: JSON.stringify(payload),
});

let body;
try {
  body = await res.json();
} catch {
  console.error('Cache purge failed: non-JSON response');
  process.exit(1);
}

if (!res.ok || (body?.ok !== true && body?.success !== true)) {
  console.error('Cache purge failed');
  console.error(JSON.stringify(body, null, 2));
  process.exit(1);
}

console.log('Cache purge succeeded');
console.log(JSON.stringify(body, null, 2));
