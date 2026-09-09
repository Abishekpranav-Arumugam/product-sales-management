import asyncio
import httpx
import time
from collections import Counter

TARGET_URL = "http://localhost:8000/sales/"
CONCURRENT_REQUESTS = 10000
MAX_CONCURRENT_CONNECTIONS = 200

sem = asyncio.Semaphore(MAX_CONCURRENT_CONNECTIONS)


async def register_and_login_user(client: httpx.AsyncClient):
    payload = {
        "email": "loadtest_user@example.com",
        "password": "Secret123@",
        "role": "user"
    }
    # Attempt registration (ignore errors if user already exists)
    # await client.post(
    #     "http://localhost:8000/auth/register", json=payload
    # )

    # Attempt login
    resp = await client.post(
        "http://localhost:8000/auth/login", json=payload
    )

    # === Code updated here (Safe JSON error handling) ===
    if resp.status_code != 200:
        raise RuntimeError(
            f"Login failed with status {resp.status_code}: {resp.text}"
        )

    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
    # ===================================================


async def send_sale_request(client: httpx.AsyncClient, headers: dict):
    payload = {
        "product_id": 1,
        "quantity": 1
    }
    async with sem:
        try:
            resp = await client.post(
                TARGET_URL, json=payload, headers=headers, timeout=15.0
            )
            return resp.status_code
        except Exception:
            return 500


async def main():
    limits = httpx.Limits(
        max_keepalive_connections=MAX_CONCURRENT_CONNECTIONS,
        max_connections=MAX_CONCURRENT_CONNECTIONS
    )
    async with httpx.AsyncClient(limits=limits) as client:
        headers = await register_and_login_user(client)

        print(f"Starting load test with {CONCURRENT_REQUESTS} requests...")
        start_time = time.time()

        tasks = [
            send_sale_request(client, headers)
            for _ in range(CONCURRENT_REQUESTS)
        ]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        elapsed = end_time - start_time

        success_count = results.count(202)
        error_count = len(results) - success_count

        code_counts = Counter(results)

        print("\n=== Load Test Results ===")
        print(f"Total Requests: {len(results)}")
        print(f"Successful (202 Accepted): {success_count}")
        print(f"Failures/Errors: {error_count}")
        print(f"Response codes received: {dict(code_counts)}")
        print(f"Time Taken: {elapsed:.2f} seconds")
        print(f"Throughput: {len(results) / elapsed:.2f} req/sec")


if __name__ == "__main__":
    asyncio.run(main())