#!/usr/bin/env python3
import argparse
import os

import sys
import time

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
APP_PATH = os.path.join(PROJECT_PATH, "app")
PYTHON = os.path.join(PROJECT_PATH, "env/bin/python3")
sys.path.append(APP_PATH)

for p in os.listdir(os.path.join(PROJECT_PATH, "env/lib/")):
    PYTHON_LIB = os.path.join(PROJECT_PATH, "env/lib/%s/site-packages" % p)
    sys.path.append(PYTHON_LIB)

from app import (
    configs,
    smartdb,
    crud
)


def init_db(ec):
    if "sqlite://" in ec.db_uri:
        directory = os.path.dirname(ec.db_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

    smart = smartdb.SmartClient(ec.db_uri)
    tries = 60
    for i in range(tries):
        try:
            smart.create_base()

            @smartdb.cockroach_transaction
            def op():
                with smart.new_session() as session:
                    crud.health_check_purge(session)

            op()
            return
        except ConnectionError as e:
            print("%d/%d %s" % (i + 1, tries, e))
            time.sleep(1)

    raise ConnectionError(ec.db_uri)


def init_journal_dir(ec):
    if not os.path.exists(ec.ignition_journal_dir):
        os.makedirs(ec.ignition_journal_dir)


def gunicorn(ec):
    cmd = [
        "%s/env/bin/gunicorn" % PROJECT_PATH,
        "--chdir",
        APP_PATH,
        "api:APP",
        "--worker-class",
        ec.gunicorn_worker_type,
        "-b",
        ec.gunicorn_bind,
        "--log-level",
        ec.logging_level.lower(),
        "-w",
        "%s" % ec.gunicorn_workers,
    ]
    print("exec[%s] -> %s\n" % (os.getpid(), " ".join(cmd)))
    with open(ec.gunicorn_pid_file, "w") as f:
        f.write("%d" % os.getpid())
    if not os.environ.get('prometheus_multiproc_dir'):
        os.environ["prometheus_multiproc_dir"] = ec.prometheus_multiproc_dir
    try:
        for f in os.listdir(ec.prometheus_multiproc_dir):
            os.remove(os.path.join(ec.prometheus_multiproc_dir, f))
    except FileNotFoundError:
        os.makedirs(ec.prometheus_multiproc_dir)
    os.execve(cmd[0], cmd, os.environ)


def matchbox(ec):
    cmd = [
        "%s/runtime/matchbox/matchbox" % PROJECT_PATH,
        "-address",
        ec.matchbox_uri.replace("https://", "").replace("http://", ""),
        "-assets-path",
        "%s" % ec.matchbox_assets,
        "-data-path",
        "%s" % ec.matchbox_path,
        "-log-level",
        ec.matchbox_logging_level.lower(),
    ]
    print("exec[%s] -> %s\n" % (os.getpid(), " ".join(cmd)))
    with open(ec.matchbox_pid_file, "w") as f:
        f.write("%d" % os.getpid())
    os.execve(cmd[0], cmd, os.environ)


def plan(ec):
    cmd = [
        PYTHON,
        "%s/plans/k8s_2t.py" % APP_PATH,
    ]
    print("exec[%s] -> %s\n" % (os.getpid(), " ".join(cmd)))
    with open(ec.plan_pid_file, "w") as f:
        f.write("%d" % os.getpid())
    os.execve(cmd[0], cmd, os.environ)


def validate():
    cmd = [
        PYTHON,
        "%s/validate.py" % PROJECT_PATH,
    ]
    print("exec[%s] -> %s\n" % (os.getpid(), " ".join(cmd)))
    os.execve(cmd[0], cmd, os.environ)


def show_configs(ec):
    for k, v in ec.__dict__.items():
        print("%s=%s" % (k, v))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Enjoliver')
    parser.add_argument('task', type=str, choices=["gunicorn", "plan", "matchbox", "show-configs", "validate"],
                        help="Choose the task to run")
    parser.add_argument('--configs', type=str, default="%s/configs.yaml" % APP_PATH,
                        help="Choose the yaml config file")
    task = parser.parse_args().task
    f = parser.parse_args().configs
    ec = configs.EnjoliverConfig(yaml_full_path=f, importer=__file__)
    if task == "gunicorn":
        init_db(ec)
        init_journal_dir(ec)
        gunicorn(ec)
    elif task == "plan":
        plan(ec)
    elif task == "matchbox":
        matchbox(ec)
    elif task == "show-configs":
        show_configs(ec)
    elif task == "validate":
        validate()
    else:
        raise AttributeError("%s not a choice" % task)
