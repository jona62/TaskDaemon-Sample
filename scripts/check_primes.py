#!/usr/bin/env python3
"""Submit prime tasks through the sample API and verify their final results."""

import argparse
import concurrent.futures
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
import uuid


class CheckError(Exception):
    pass


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def positive_seconds(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a positive finite number")
    return number


def prime_limit(value):
    number = int(value)
    if not 2 <= number <= 10_000_000:
        raise argparse.ArgumentTypeError("must be between 2 and 10000000")
    return number


def request(url, timeout, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, UnicodeError, OSError) as exc:
        if isinstance(exc, urllib.error.HTTPError):
            exc.close()
        raise CheckError(f"request failed for {url}: {exc}") from exc


def request_json(url, timeout, payload=None):
    body = request(url, timeout, payload)
    try:
        value = json.loads(body)
    except json.JSONDecodeError as exc:
        raise CheckError(f"invalid JSON from {url}") from exc
    if not isinstance(value, dict):
        raise CheckError(f"expected a JSON object from {url}")
    return value


def remaining_timeout(deadline, request_timeout):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise CheckError("deadline reached before all tasks completed")
    return min(remaining, request_timeout)


def validate_result(task_id, task, limit):
    if task.get("id") != task_id or task.get("task_type") != "prime":
        raise CheckError(f"unexpected task details for {task_id}")
    result = task.get("result")
    if not isinstance(result, dict) or result.get("limit") != limit:
        raise CheckError(f"unexpected result limit for {task_id}: {result}")
    count, largest = result.get("count"), result.get("largest")
    if type(count) is not int or type(largest) is not int or not (1 <= count <= limit and 2 <= largest <= limit):
        raise CheckError(f"invalid prime result for {task_id}: {result}")
    expected = {2: (1, 2), 100: (25, 97), 1_000_000: (78_498, 999_983), 10_000_000: (664_579, 9_999_991)}
    if limit in expected and (count, largest) != expected[limit]:
        raise CheckError(f"incorrect prime result for {task_id}: {result}")


def submit_task(args, deadline):
    response = request_json(
        args.api_url.rstrip("/") + "/prime",
        remaining_timeout(deadline, args.request_timeout),
        {"limit": args.limit},
    )
    task_id = response.get("task_id")
    try:
        if not isinstance(task_id, str) or str(uuid.UUID(task_id)) != task_id:
            raise ValueError("task ID must be a canonical UUID")
    except ValueError as exc:
        raise CheckError(f"invalid submission response: {response}") from exc
    return task_id


def poll_task(args, deadline, task_id):
    task = request_json(
        args.daemon_url.rstrip("/") + "/api/tasks/" + task_id,
        remaining_timeout(deadline, args.request_timeout),
    )
    status = task.get("status")
    if status == "failed":
        raise CheckError(f"task {task_id} failed: {task.get('last_error')}")
    if status == "completed":
        validate_result(task_id, task, args.limit)
        return task_id
    if status not in ("pending", "processing"):
        raise CheckError(f"task {task_id} has unexpected status: {status}")
    return None


def check(args):
    # Check prerequisites before submitting work; never start resources here.
    request(args.api_url.rstrip("/") + "/health", args.request_timeout)
    health = request_json(args.daemon_url.rstrip("/") + "/health", args.request_timeout)
    if health.get("status") != "healthy":
        raise CheckError(f"TaskDaemon is unhealthy: {health}")

    started = time.monotonic()
    deadline = started + args.timeout
    task_ids = set()
    submission_errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        submissions = [executor.submit(submit_task, args, deadline) for _ in range(args.tasks)]
        for future in concurrent.futures.as_completed(submissions):
            try:
                task_id = future.result()
                if task_id in task_ids:
                    raise CheckError(f"duplicate task ID returned: {task_id}")
                task_ids.add(task_id)
            except CheckError as exc:
                submission_errors.append(str(exc))
        submitted_at = time.monotonic()
        if submission_errors:
            raise CheckError(f"submission failed; {len(task_ids)} tasks accepted: {submission_errors[0]}")
        print(f"Submitted {len(task_ids)} tasks in {submitted_at - started:.3f}s", flush=True)
        pending = task_ids.copy()
        while pending:
            polls = [executor.submit(poll_task, args, deadline, task_id) for task_id in pending]
            for future in concurrent.futures.as_completed(polls):
                completed = future.result()
                if completed is not None:
                    pending.remove(completed)
            if pending:
                time.sleep(min(args.poll_interval, remaining_timeout(deadline, args.poll_interval)))
    elapsed = time.monotonic() - started
    print(f"Verified {len(task_ids)} completed tasks in {elapsed:.3f}s total ({len(task_ids) / elapsed:.2f} tasks/s)")
    print("Total includes submission and status polling; workers run while requests are submitted.")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=positive_int, default=1)
    parser.add_argument("--concurrency", type=positive_int, default=4)
    parser.add_argument("--limit", type=prime_limit, default=1_000_000)
    parser.add_argument("--timeout", type=positive_seconds, default=120)
    parser.add_argument("--request-timeout", type=positive_seconds, default=10)
    parser.add_argument("--poll-interval", type=positive_seconds, default=0.2)
    parser.add_argument("--api-url", default=os.environ.get("API_URL", "http://localhost:8081"))
    parser.add_argument("--daemon-url", default=os.environ.get("DAEMON_URL", "http://localhost:8080"))
    return parser.parse_args(argv)


def main():
    try:
        check(parse_args())
    except CheckError as exc:
        print(f"ERROR: {exc}. Start the sample explicitly with docker compose up --build, then check its logs if needed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
