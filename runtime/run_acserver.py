#!/usr/bin/env python3
import multiprocessing
import os.path
import subprocess
import sys

import requests

RUNTIME_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.dirname(RUNTIME_PATH)

sys.path.append(PROJECT_PATH)
sys.path.append(RUNTIME_PATH)

for p in os.listdir(os.path.join(PROJECT_PATH, "env/lib/")):
    PYTHON_LIB = os.path.join(PROJECT_PATH, "env/lib/%s/site-packages" % p)
    sys.path.append(PYTHON_LIB)

from runtime import (
    config,
)
import psutil


def start_acserver():
    cmd = ["%s/acserver/acserver" % RUNTIME_PATH, "%s/ac-config.yml" % RUNTIME_PATH]
    os.execve(cmd[0], cmd, os.environ)


class AcserverError(Exception):
    pass


if __name__ == '__main__':
    if os.geteuid() != 0:
        raise PermissionError("start as root")
    with open("/dev/null", 'w') as null:
        code = subprocess.call(["ip", "addr", "show", "rack0"], stdout=null)
        if code != 0:
            config.rkt_path_d(RUNTIME_PATH)
            config.rkt_stage1_d(RUNTIME_PATH)
            config.dgr_config(RUNTIME_PATH)
            config.acserver_config(RUNTIME_PATH)
            subprocess.check_call([
                "%s/rkt/rkt" % RUNTIME_PATH,
                "--local-config=%s" % RUNTIME_PATH,
                "--net=rack0",
                "run",
                "--insecure-options=all",
                "coreos.com/rkt/stage1-coreos",
                "--exec",
                "/bin/bash",
                "--", "-c", "exit", "0"])

    try:
        resp = requests.get("http://172.20.0.1/enjoliver.local/")
        resp.close()
        if resp.status_code != 200:
            raise AcserverError("status code: %s != 200" % resp.status_code)
        with open("%s/acserver.pid" % RUNTIME_PATH, 'r') as f:
            pid = f.read()
        p = psutil.Process(int(pid))
        print("%s %s running: %s" % (pid, p.name(), p.is_running()))

    except requests.exceptions.ConnectionError:
        acserver_p = multiprocessing.Process(target=start_acserver)
        acserver_p.start()
        with open("%s/acserver.pid" % RUNTIME_PATH, "w") as f:
            f.write(acserver_p.pid.__str__())
        try:
            acserver_p.join()
        except KeyboardInterrupt:
            acserver_p.terminate()
            acserver_p.join(1)
            with open("%s/acserver.pid" % RUNTIME_PATH, "w") as f:
                pass
