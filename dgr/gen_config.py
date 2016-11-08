#! /usr/bin/env python
import os

if __name__ == "__main__":

    CWD = os.path.dirname(os.path.abspath(__file__))

    print "Generate config with CWD=%s" % CWD

    with open("%s/config.yml.template" % CWD, "r") as template:
        with open("%s/config.yml" % CWD, "w") as config:
            for l in template:
                config.write(l.replace("__FULLPATH__", CWD))

    with open("%s/path.d/paths.json.template" % CWD, "r") as template:
        with open("%s/path.d/paths.json" % CWD, "w") as config:
            for l in template:
                config.write(l.replace("__FULLPATH__", CWD))
