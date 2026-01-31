# Load tests (k6)

Load tests for the URL shortener API using [k6](https://k6.io/).

## Prerequisites

Install k6:

- **macOS (Homebrew):** `brew install k6`
- **Linux:** see [k6 install docs](https://grafana.com/docs/k6/latest/set-up/install-k6/)
- **Docker (from repo root, stdin):**  
  `docker run --rm -i grafana/k6 run - < tests/load/redirect_test.js`  
  (API must be reachable from host; use `BASE_URL` if needed.)
- **Docker (with volume):**  
  Use **`BASE_URL=http://host.docker.internal:8000`** so the container can reach the API on your machine (macOS/Windows). Paths with spaces must be quoted:
  ```bash
  docker run --rm -v "$(pwd)/tests/load:/tests" \
    -e BASE_URL=http://host.docker.internal:8000 \
    grafana/k6 run /tests/redirect_test.js
  ```

## Run redirect load test

1. Start the API (and Docker services if needed):

   ```bash
   ./scripts/docker-up.sh
   uvicorn app.main:app --reload
   ```

2. From the project root:

   ```bash
   k6 run tests/load/redirect_test.js
   ```

3. With custom base URL and duration:

   ```bash
   k6 run -e BASE_URL=http://localhost:8000 -e DURATION=30s tests/load/redirect_test.js
   ```

4. With more virtual users and longer run:

   ```bash
   k6 run --vus 20 --duration 60s tests/load/redirect_test.js
   ```

## What the redirect test does

- **Setup:** Creates 10 short URLs via `POST /api/v1/shorten` and collects their `short_code`s.
- **Default:** Each VU repeatedly picks a random short code and calls `GET /{short_code}` (no follow redirect).
- **Checks:** Status 307 and presence of `Location` header.
- **Stages:** Ramp up → 10 VUs → hold → ramp down.
- **Thresholds:** 95th percentile latency < 500 ms, error rate < 1%.
