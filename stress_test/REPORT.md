# Stress test report

## Environment
- OS: Windows 11 Pro
- CPU: 12th Gen Intel(R) Core(TM) i5-1235U
- RAM: 24 GB
- Docker: Docker version 28.4.0, build d8eb465
- Python: 3.8.10
- Locust: 2.25.0 (headless)

## Scenario
- Users (`-u`): 50
- Spawn rate (`-r`): 10/s
- Duration (`-t`): 2m
- Host: http://localhost:8000
- Endpoints:
  - Index: **GET /docs**
  - Auth: **POST /login**
  - Prediction: **POST /model/predict** (imagen `dog.jpeg` + `Authorization: Bearer <token>`)

## Results

| Run     | Users | Spawn/s | RPS (Agg) | p50 (ms) | p95 (ms) | p99 (ms) | Avg (ms) | Max (ms) | Fail %  |
|---------|-------|---------|-----------|----------|----------|----------|----------|----------|---------|
| model=1 | 50    | 10      | 6.37      | 7500     | 15000    | 16000    | 6867     | 15071    | 33.03%  |
| model=2 | 50    | 10      | 5.17      | 6600     | 20000    | 25000    | 8156     | 24644    | 43.28%  |

## Comment (brief)
When scaling to **2** instances of `model` throughput did not increase (RPS ↓ de 6.37 a 5.17) and high latencies (p95/p99) went up, with a higher failure rate. This indicates a bottleneck outside the container of `model` (e.g, API/tail/connections) and connection closures under load. 
