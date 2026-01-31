/**
 * k6 load test: Redirect endpoint (GET /{short_code})
 *
 * Run (local k6):
 *   k6 run tests/load/redirect_test.js
 *
 * Run (Docker; API on host): use host.docker.internal so container reaches your machine:
 *   docker run --rm -v "$(pwd)/tests/load:/tests" \
 *     -e BASE_URL=http://host.docker.internal:8000 \
 *     grafana/k6 run /tests/redirect_test.js
 *
 * With more VUs:
 *   k6 run --vus 20 --duration 60s tests/load/redirect_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Threshold strings built at runtime so TS/JSX parsers don't misread "<" as a tag
const THRESHOLD_P95_LATENCY = 'p(95)' + '<' + '500';
const THRESHOLD_ERROR_RATE = 'rate' + '<' + '0.01';

export const options = {
  stages: [
    { duration: '10s', target: 5 },   // Ramp up to 5 VUs
    { duration: '30s', target: 10 }, // Ramp up to 10 VUs
    { duration: '20s', target: 10 },  // Stay at 10 VUs
    { duration: '10s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: [THRESHOLD_P95_LATENCY],
    http_req_failed: [THRESHOLD_ERROR_RATE],
  },
};

/**
 * Setup: create short URLs via API so we have valid codes to redirect.
 * Uses a single well-known URL (returns 200 for HEAD) to avoid validation failures.
 * Returns { shortCodes: string[] } for the main test.
 */
export function setup() {
  const shortCodes = [];
  const createUrl = `${BASE_URL}/api/v1/shorten`;
  // URL that passes API reachability check (HEAD must return 200)
  const targetUrl = 'https://www.example.com';
  let lastStatus = 0;
  let lastBody = '';

  for (let i = 0; i < 10; i++) {
    const payload = JSON.stringify({ url: targetUrl });
    const res = http.post(createUrl, payload, {
      headers: { 'Content-Type': 'application/json' },
    });
    lastStatus = res.status;
    lastBody = res.body || '';
    if (res.status === 201) {
      try {
        const body = JSON.parse(res.body);
        if (body.short_code) shortCodes.push(body.short_code);
      } catch (_) {
        // ignore parse error
      }
    }
  }

  if (shortCodes.length === 0) {
    throw new Error(
      `Setup failed: no short codes created. Last response: ${lastStatus} - ${lastBody.substring(0, 200)}. ` +
      'Is the API running at BASE_URL? Does POST /api/v1/shorten return 201?'
    );
  }
  return { shortCodes };
}

export default function (data) {
  const { shortCodes } = data;
  const code = shortCodes[Math.floor(Math.random() * shortCodes.length)];
  const url = `${BASE_URL}/${code}`;

  const res = http.get(url, { redirects: 0 });

  const ok = check(res, {
    'status is 307': (r) => r.status === 307,
    'has Location header': (r) => r.headers.Location && r.headers.Location.length > 0,
  });

  if (!ok) {
    console.warn(`Redirect failed: ${res.status} ${url} body=${res.body?.substring(0, 80)}`);
  }

  sleep(0.5 + Math.random() * 0.5); // 0.5–1s between requests per VU
}
