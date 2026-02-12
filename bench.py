import json
import time
import urllib.request
import concurrent.futures

URL = "http://127.0.0.1:8000/chat"

def post(session_id: str, message: str) -> dict:
    payload = {"session_id": session_id, "message": message}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))

def one_flow(i: int) -> list[dict]:
    sid = f"bench_{i}"
    r1 = post(sid, "我想查订单")
    r2 = post(sid, "abc")
    r3 = post(sid, "123456")
    return [r1, r2, r3]

def main():
    concurrency = 5  # 你可以改成 10
    t0 = time.time()
    latencies = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = [ex.submit(one_flow, i) for i in range(concurrency)]
        for fut in concurrent.futures.as_completed(futs):
            flows = fut.result()
            for r in flows:
                latencies.append(r.get("latency_ms", 0))

    t1 = time.time()
    latencies.sort()
    avg = sum(latencies) / max(1, len(latencies))
    p50 = latencies[len(latencies)//2] if latencies else 0
    p95 = latencies[int(len(latencies)*0.95)-1] if len(latencies) >= 20 else (latencies[-1] if latencies else 0)

    print(f"concurrency={concurrency}, requests={len(latencies)}, total_time_s={t1-t0:.2f}")
    print(f"latency_ms avg={avg:.1f}, p50={p50}, p95={p95}, max={max(latencies) if latencies else 0}")

if __name__ == "__main__":
    main()
