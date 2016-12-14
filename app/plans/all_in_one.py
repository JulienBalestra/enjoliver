#! /usr/bin/env python
import os

import sys

try:
    import generator
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import generator


def all_in_one(marker):
    gen = generator.Generator(
        profile_id="%s" % marker,
        name="%s" % marker,
        ignition_id="%s.yaml" % marker,
        bootcfg_path=os.getenv("BOOTCFG_PATH", "/var/lib/bootcfg"),
        extra_metadata={
            "etcd_name": "all-in-one",
            "etcd_initial_cluster": "all-in-one=http://127.0.0.1:2380",
            "etcd_initial_advertise_peer_urls": "http://127.0.0.1:2380",
            "etcd_advertise_client_urls": "http://127.0.0.1:2379",
            "k8s_apiserver_count": 1,
            "k8s_advertise_ip": "0.0.0.0",
        }
    )
    gen.dumps()


if __name__ == '__main__':
    marker = "k8s-all-in-one"
    assert os.getenv("BOOTCFG_IP", None) is not None
    assert os.getenv("API_IP", None) is not None
    all_in_one(marker)
