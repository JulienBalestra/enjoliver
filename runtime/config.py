#! /usr/bin/env python
import json
import os


def rkt_path_d(path):
    data = {
        "rktKind": "paths",
        "rktVersion": "v1",
        "data": "%s/data" % path,
        "stage1-images": "%s/rkt" % path
    }
    try:
        os.makedirs("%s/paths.d/" % path)
    except OSError:
        pass
    try:
        os.makedirs("%s/data/" % path)
    except OSError:
        pass

    with open("%s/paths.d/paths.json" % path, "w") as f:
        json.dump(data, f)


def dgr_config(path):
    data = [
        "targetWorkDir: %s/target" % path,
        "rkt:",
        "  path: %s/rkt/rkt" % path,
        "  insecureOptions: [http, image]",
        "  dir: %s/data" % path,
        "  localConfig: %s" % path,
        "  systemConfig: %s" % path,
        "  userConfig: %s" % path,
        "  trustKeysFromHttps: false",
        "  noStore: false",
        "  storeOnly: false",
        "push:",
        '  url: "http://enjoliver.local"',
    ]
    with open("%s/config.yml" % path, "w") as f:
        f.write("\n".join(data) + "\n")


def acserver_config(path):
    data = [
        "api:",
        "  port: 80",
        "storage:",
        "  unsigned: true",
        "  allowOverride: true",
        '  rootPath: %s/acserver.d' % path,
    ]
    with open("%s/ac-config.yml" % path, "w") as f:
        f.write("\n".join(data) + "\n")
    with open("/etc/hosts") as f:
        for l in f:
            if "enjoliver.local" in l:
                return
    try:
        with open("/etc/hosts", 'a') as f:
            f.write("127.0.0.1 enjoliver.local # added by %s\n" % os.path.abspath(__file__))
    except IOError:
        os.write(2, "/etc/hosts ignore: run as sudo")


if __name__ == "__main__":
    pwd = os.path.dirname(os.path.abspath(__file__))
    rkt_path_d(pwd)
    dgr_config(pwd)
    acserver_config(pwd)
