#!/usr/bin/python
import argparse
import os

import sys

project_path = os.path.dirname(os.path.abspath(__file__))
app_path = os.path.join(project_path, "app")
python = os.path.join(project_path, "env/bin/python")
site_packages_path = os.path.join(project_path, "env/local/lib/python2.7/site-packages")

sys.path.append(app_path)
sys.path.append(site_packages_path)

from app import (
    configs,
    model
)

ec = configs.EnjoliverConfig()


def init_db():
    import sqlalchemy
    engine = sqlalchemy.create_engine(ec.db_uri)
    model.Base.metadata.create_all(engine)


def gunicorn():
    cmd = [
        "%s/env/bin/gunicorn" % project_path,
        "--chdir",
        app_path,
        "api:app",
        'egg:meinheld#gunicorn_worker',
        "-b",
        "0.0.0.0:5000",
        "--log-level",
        ec.logging_level.lower(),
        "-w",
        "%s" % ec.gunicorn_workers
    ]
    os.write(1, "PID  -> %s\n"
                "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
    os.execve(cmd[0], cmd, os.environ)


def matchbox():
    cmd = [
        "%s/runtime/matchbox/matchbox" % project_path,
        "-assets-path",
        "%s" % ec.matchbox_assets,
        "-data-path",
        "%s" % ec.matchbox_path,
        "-log-level",
        ec.logging_level.lower()
    ]
    os.write(1, "PID  -> %s\n"
                "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
    os.execve(cmd[0], cmd, os.environ)


def plan():
    cmd = [
        python,
        "%s/plans/k8s_2t.py" % app_path
    ]
    os.write(1, "PID  -> %s\n"
                "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
    os.execve(cmd[0], cmd, os.environ)


def show_config():
    for k, v in ec.__dict__.iteritems():
        print "%s=%s" % (k, v)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Enjoliver')
    parser.add_argument('task', type=str, choices=["gunicorn", "plan", "matchbox", "show-config"],
                        help="Choose your task to run")
    task = parser.parse_args().task
    if task == "gunicorn":
        init_db()
        gunicorn()
    elif task == "plan":
        plan()
    elif task == "matchbox":
        matchbox()
    elif task == "show-config":
        show_config()
    else:
        raise AttributeError("%s not a choice" % task)
