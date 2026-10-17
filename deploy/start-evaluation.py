"""Supervise a loopback-only graph and public API in one ephemeral free service."""

import os
import signal
import shutil
import tempfile
import subprocess
import sys
import time
from redis import Redis
from redis.exceptions import RedisError


def main():
    os.environ.update(
        FALKOR_HOST="127.0.0.1",
        FALKOR_PORT="6379",
        FALKOR_PASSWORD="",
        FALKOR_USERNAME="",
    )
    runtime = tempfile.mkdtemp(prefix="chronos-evaluation-")
    shutil.copyfile("/app/reference/dump.rdb", runtime + "/dump.rdb")
    children = []
    stopping = False

    def stop(signum=None, frame=None):
        nonlocal stopping
        stopping = True
        for process in reversed(children):
            if process.poll() is None:
                process.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        graph = subprocess.Popen(
            [
                "redis-server",
                "--bind",
                "127.0.0.1",
                "--port",
                "6379",
                "--dir",
                runtime,
                "--protected-mode",
                "yes",
                "--appendonly",
                "no",
                "--save",
                "",
                "--loadmodule",
                "/usr/local/lib/falkordb.so",
                "THREAD_COUNT",
                "2",
                "OMP_THREAD_COUNT",
                "1",
                "--logfile",
                "/tmp/chronos-graph.log",
            ]
        )
        children.append(graph)
        db = Redis(host="127.0.0.1", port=6379, socket_connect_timeout=1)
        for _ in range(100):
            if stopping or graph.poll() is not None:
                raise RuntimeError("Evaluation database did not start.")
            try:
                if db.ping():
                    break
            except (RedisError, OSError):
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("Evaluation database startup timed out.")
        db.close()
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "chronos.public:create_app",
                "--factory",
                "--host",
                "0.0.0.0",
                "--port",
                os.environ.get("PORT", "8000"),
                "--workers",
                "1",
                "--proxy-headers",
                "--forwarded-allow-ips",
                "*",
                "--no-access-log",
            ]
        )
        children.append(server)
        while not stopping and all(p.poll() is None for p in children):
            time.sleep(0.3)
        return 0 if stopping else 1
    finally:
        stop()
        for process in children:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
