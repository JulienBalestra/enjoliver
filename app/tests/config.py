#! /usr/bin/env python
import json
import os


def rkt_path_d(test_d, runtime_d):
    data = {
        "rktKind": "paths",
        "rktVersion": "v1",
        "data": "%s/data" % runtime_d,
        "stage1-images": "%s/rkt" % runtime_d
    }
    try:
        os.makedirs("%s/paths.d/" % test_d)
    except OSError:
        pass
    try:
        os.makedirs("%s/data/" % runtime_d)
    except OSError:
        pass

    with open("%s/paths.d/paths.json" % test_d, "w") as f:
        json.dump(data, f)


if __name__ == "__main__":
    test_d = os.path.dirname(os.path.abspath(__file__))
    app_d = os.path.dirname(test_d)
    project_d = os.path.dirname(app_d)
    rkt_path_d(test_d, "%s/runtime" % project_d)
