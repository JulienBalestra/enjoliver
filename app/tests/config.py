#! /usr/bin/env python
import json
import os


def rkt_path_d(test_d, runtime_d):
    rkt_data = "/tmp/rkt-data"
    data = {
        "rktKind": "paths",
        "rktVersion": "v1",
        "data": rkt_data,
        "stage1-images": "%s/rkt" % runtime_d
    }
    try:
        os.makedirs("%s/paths.d/" % test_d)
    except OSError:
        pass
    try:
        os.makedirs(rkt_data)
    except OSError:
        pass

    with open("%s/paths.d/paths.json" % test_d, "w") as f:
        json.dump(data, f)


if __name__ == "__main__":
    test_d = os.path.dirname(os.path.abspath(__file__))
    app_d = os.path.dirname(test_d)
    project_d = os.path.dirname(app_d)
    rkt_path_d(test_d, "%s/runtime" % project_d)
