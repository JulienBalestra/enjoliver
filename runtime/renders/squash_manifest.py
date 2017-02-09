#! /usr/bin/env python
import argparse
import datetime
import json

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("manifest", help="Path to app container Manifest")
    m = args.parse_args().manifest
    print m
    with open(m, 'r') as f:
        manifest = json.load(f)

    print json.dumps(manifest, indent=2)

    try:
        if len(manifest["dependencies"]) > 0:
            manifest["dependencies"] = []

            manifest["annotations"].append({
                "name": "squash-date",
                "value": "%s" % datetime.datetime.now()
            })

            print json.dumps(manifest, indent=2)

            with open(m, 'w') as f:
                json.dump(manifest, f)

    except KeyError:
        print "KeyError with dependencies"

    print "No dependencies or already render/squashed"
