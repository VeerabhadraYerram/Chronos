"""Build a clean reference-only RDB from code, never from a visitor workspace."""

import os
import subprocess
import time
from pathlib import Path
from redis import Redis
from redis.exceptions import RedisError

os.environ.update(FALKOR_HOST="127.0.0.1", FALKOR_PORT="6379", FALKOR_PASSWORD="")
snapshot = Path("/app/reference")
snapshot.mkdir(parents=True, exist_ok=True)
p = subprocess.Popen(
    [
        "redis-server",
        "--bind",
        "127.0.0.1",
        "--port",
        "6379",
        "--save",
        "",
        "--appendonly",
        "no",
        "--dir",
        str(snapshot),
        "--logfile",
        "/tmp/build-graph.log",
        "--loadmodule",
        "/usr/local/lib/falkordb.so",
        "THREAD_COUNT",
        "2",
        "OMP_THREAD_COUNT",
        "1",
    ]
)
try:
    db = Redis(host="127.0.0.1", port=6379, socket_timeout=10)
    for _ in range(100):
        try:
            if db.ping():
                break
        except (RedisError, OSError):
            pass
        time.sleep(0.1)
    else:
        raise RuntimeError("Reference build database did not start")
    from chronos.company.store import CompanyStore, BASE_NAME

    store = CompanyStore(BASE_NAME)
    store.seed()
    assert store.stats()["labels"]["Client"] == 12
    assert not store.read("MATCH (r:Receipt) RETURN count(r)")[0][0]
    assert not store.read("MATCH (s:DemoSession) RETURN count(s)")[0][0]
    db.save()
    assert (snapshot / "dump.rdb").is_file()
    print(
        "Reference snapshot built from source fixture; no visitor history or provider calls."
    )
finally:
    p.terminate()
    p.wait(timeout=15)
