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
        "  insecureOptions: [image]",
        "  dir: %s/data" % path,
        "  localConfig: %s" % path,
        "  systemConfig: %s" % path,
        "  userConfig: %s" % path,
        "  trustKeysFromHttps: false",
        "  noStore: false",
        "  storeOnly: false"
    ]
    with open("%s/config.yml" % path, "w") as f:
        f.write("\n".join(data) + "\n")


if __name__ == "__main__":
    pwd = os.path.dirname(os.path.abspath(__file__))
    rkt_path_d(pwd)
    dgr_config(pwd)
