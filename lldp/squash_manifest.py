#! /usr/bin/env python
import json
import os

if __name__ == "__main__":
    CWD = os.path.dirname(os.path.abspath(__file__))

    manifest_file = "%s/lldp.render/manifest" % CWD
    print "Squash manifest: dependencies -> %s" % manifest_file

    with open(manifest_file, 'r') as f:
        manifest = json.load(f)
    manifest["dependencies"] = []
    manifest["annotations"].append({
        "name": "squashed-for",
        "value": "static"
    })

    print json.dumps(manifest, indent=2)

    with open(manifest_file, 'w') as f:
        json.dump(manifest, f)
