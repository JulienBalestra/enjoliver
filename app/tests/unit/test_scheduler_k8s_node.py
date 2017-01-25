import json
import os
import subprocess
import unittest

from app import scheduler


class TestSchedulerK8sNode(unittest.TestCase):
    __name__ = "TestEtcdScheduler"
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    app_path = "%s" % os.path.split(tests_path)[0]
    project_path = "%s" % os.path.split(app_path)[0]
    test_bootcfg_path = "%s/test_bootcfg" % tests_path

    @classmethod
    def setUpClass(cls):
        subprocess.check_output(["make", "-C", cls.project_path])
        scheduler.EtcdProxyScheduler.apply_deps_tries = 1
        scheduler.EtcdProxyScheduler.apply_deps_delay = 0

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (TestSchedulerK8sNode.test_bootcfg_path, k)
                for k in ("profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.write(1, "\r-> remove %s\n\r" % f)
                    os.remove("%s/%s" % (d, f))

    @staticmethod
    def get_something(things):
        l = []
        d = "%s/%s" % (TestSchedulerK8sNode.test_bootcfg_path, things)
        for f in os.listdir(d):
            if ".gitkeep" == f:
                continue
            with open("%s/%s" % (d, f), 'r') as j:
                content = j.read()
            l.append(json.loads(content))
        return l

    @staticmethod
    def get_profiles():
        return TestSchedulerK8sNode.get_something("profiles")

    @staticmethod
    def get_groups():
        return TestSchedulerK8sNode.get_something("groups")

    def setUp(self):
        self.clean_sandbox()
        pass

    def test_00_get_ip(self):
        m = {
            "boot-info": {
                "mac": "52:54:00:95:24:0f",
                "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
            },
            "interfaces": [
                {
                    "cidrv4": "127.0.0.1/8",
                    "ipv4": "127.0.0.1",
                    "mac": "",
                    "name": "lo",
                    "netmask": 8
                },
                {
                    "cidrv4": "172.20.0.57/16",
                    "ipv4": "172.20.0.57",
                    "mac": "52:54:00:95:24:0f",
                    "name": "eth0",
                    "netmask": 21, "gateway": "172.20.0.1"}
            ],
            "lldp": {
                "data": {
                    "interfaces": [
                        {
                            "chassis": {
                                "id": "28:f1:0e:12:20:00",
                                "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                            },
                            "port": {
                                "id": "fe:54:00:95:24:0f"
                            }
                        }
                    ]
                },
                "is_file": True
            }
        }
        ret = scheduler.EtcdMemberScheduler.get_machine_tuple(m)
        self.assertEqual(ret, ("172.20.0.57", "52:54:00:95:24:0f", "172.20.0.57/16", "172.20.0.1"))

    def test_01_get_ip(self):
        m = {
            "boot-info": {
                "mac": "52:54:00:95:24:0a",
                "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
            },
            "interfaces": [
                {
                    "cidrv4": "127.0.0.1/8",
                    "ipv4": "127.0.0.1",
                    "mac": "",
                    "name": "lo",
                    "netmask": 8
                },
                {
                    "cidrv4": "172.20.0.57/16",
                    "ipv4": "172.20.0.57",
                    "mac": "52:54:00:95:24:0f",
                    "name": "eth0",
                    "netmask": 21, "gateway": "172.20.0.1"}
            ],
            "lldp": {
                "data": {
                    "interfaces": [
                        {
                            "chassis": {
                                "id": "28:f1:0e:12:20:00",
                                "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                            },
                            "port": {
                                "id": "fe:54:00:95:24:0f"
                            }
                        }
                    ]
                },
                "is_file": True
            }
        }
        with self.assertRaises(LookupError):
            scheduler.EtcdMemberScheduler.get_machine_tuple(m)

    # @unittest.skip("skip")
    def test_03(self):
        def fake_fetch_discovery(x):
            # 3
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.57/16",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:0f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:a4:32:b5",
                        "uuid": "7faef191-44d2-4dd9-9492-63b8cce55eae"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.83/16",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:a4:32:b5"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c2",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a4c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.70/16",
                            "ipv4": "172.20.0.70",
                            "mac": "52:54:00:c3:22:c2",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c2"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                }
            ]

        marker = "unit-%s-" % TestSchedulerK8sNode.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        self.assertTrue(sch_member.apply())
        sch_cp = scheduler.K8sControlPlaneScheduler(
            etcd_member_instance=sch_member,
            ignition_control_plane="%sk8s-control-plane" % marker
        )
        self.assertEqual(len(sch_cp.etcd_initial_cluster.split(",")), 3)
        sch_no = scheduler.K8sNodeScheduler(
            k8s_control_plane=sch_cp,
            ignition_node="%sk8s-node" % marker
        )

        self.assertEqual(len(sch_no.etcd_initial_cluster.split(",")), 3)
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 1)
        groups = self.get_groups()
        self.assertEqual(len(groups), 3)

    # @unittest.skip("skip")
    def test_04(self):
        def fake_fetch_discovery(x):
            # 3
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.57/16",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:0f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:a4:32:b5",
                        "uuid": "7faef191-44d2-4dd9-9492-63b8cce55eae"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.83/16",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:a4:32:b5"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c2",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a4c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.70/16",
                            "ipv4": "172.20.0.70",
                            "mac": "52:54:00:c3:22:c2",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c2"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                }
            ]

        marker = "unit-%s-" % TestSchedulerK8sNode.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_cp = scheduler.K8sControlPlaneScheduler(
            etcd_member_instance=sch_member,
            ignition_control_plane="%sk8scontrol-plane" % marker,
            apply_first=True
        )

        self.assertEqual(len(sch_cp.etcd_initial_cluster.split(",")), 3)
        sch_no = scheduler.K8sNodeScheduler(
            k8s_control_plane=sch_cp,
            ignition_node="%sk8s-node" % marker
        )

        self.assertEqual(len(sch_no.etcd_initial_cluster.split(",")), 3)
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 1)
        groups = self.get_groups()
        self.assertEqual(len(groups), 3)

    # @unittest.skip("skip")
    def test_05(self):
        def fake_fetch_discovery(x):
            # 3
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.57/16",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:0f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:a4:32:b5",
                        "uuid": "7faef191-44d2-4dd9-9492-63b8cce55eae"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.83/16",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:a4:32:b5"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c2",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a4c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.70/16",
                            "ipv4": "172.20.0.70",
                            "mac": "52:54:00:c3:22:c2",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c2"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                }
            ]

        marker = "unit-%s-" % TestSchedulerK8sNode.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_cp = scheduler.K8sControlPlaneScheduler(
            etcd_member_instance=sch_member,
            ignition_control_plane="%sk8s-control-plane" % marker
        )
        sch_cp.fetch_discovery = fake_fetch_discovery
        self.assertEqual(sch_cp.etcd_initial_cluster, None)
        sch_cp.apply_member()
        self.assertEqual(len(sch_cp.etcd_initial_cluster.split(",")), 3)
        sch_no = scheduler.K8sNodeScheduler(
            k8s_control_plane=sch_cp,
            ignition_node="%sk8s-node" % marker
        )
        self.assertEqual(len(sch_no.etcd_initial_cluster.split(",")), 3)
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 1)
        groups = self.get_groups()
        self.assertEqual(len(groups), 3)

    # @unittest.skip("skip")
    def test_06(self):
        def fake_fetch_discovery(x):
            # 3
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.57/16",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:0f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:a4:32:b5",
                        "uuid": "7faef191-44d2-4dd9-9492-63b8cce55eae"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.83/16",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:a4:32:b5"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c2",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a4c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.70/16",
                            "ipv4": "172.20.0.70",
                            "mac": "52:54:00:c3:22:c2",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c2"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                }
            ]

        marker = "unit-%s-" % TestSchedulerK8sNode.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_cp = scheduler.K8sControlPlaneScheduler(
            etcd_member_instance=sch_member,
            ignition_control_plane="%sk8s-control-plane" % marker,
            apply_first=True
        )
        sch_cp.fetch_discovery = fake_fetch_discovery
        self.assertEqual(len(sch_cp.etcd_initial_cluster.split(",")), 3)
        self.assertFalse(sch_cp.apply())
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 1)
        groups = self.get_groups()
        self.assertEqual(len(groups), 3)
        self.assertEqual(len(sch_cp.done_list), 0)
        scheduler.K8sNodeScheduler.apply_deps_delay = 0
        scheduler.K8sNodeScheduler.apply_deps_tries = 1
        with self.assertRaises(RuntimeError):
            scheduler.K8sNodeScheduler(
                k8s_control_plane=sch_cp,
                ignition_node="%sk8s-node" % marker,
                apply_first=True
            )

    # @unittest.skip("skip")
    def test_07_1(self):
        def fake_fetch_discovery(x):
            # 4
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.57/16",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:0f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:a4:32:b5",
                        "uuid": "7faef191-44d2-4dd9-9492-63b8cce55eae"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.83/16",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:a4:32:b5"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c2",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a4c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.70/16",
                            "ipv4": "172.20.0.70",
                            "mac": "52:54:00:c3:22:c2",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c2"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c4",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a8c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.102/16",
                            "ipv4": "172.20.0.102",
                            "mac": "52:54:00:c3:22:c4",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c4"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                }
            ]

        marker = "unit-%s-" % TestSchedulerK8sNode.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_cp = scheduler.K8sControlPlaneScheduler(
            etcd_member_instance=sch_member,
            ignition_control_plane="%sk8s-control-plane" % marker,
            apply_first=True
        )
        sch_cp.control_plane_nb = 1
        sch_cp.fetch_discovery = fake_fetch_discovery
        self.assertEqual(len(sch_cp.etcd_initial_cluster.split(",")), 3)
        self.assertEqual(len(sch_cp.done_list), 0)
        sch_no = scheduler.K8sNodeScheduler(
            k8s_control_plane=sch_cp,
            ignition_node="%sk8s-node" % marker,
            apply_first=True
        )
        self.assertEqual(len(sch_cp.done_list), 1)
        self.assertEqual(len(sch_no.wide_done_list), 4)

    # @unittest.skip("skip")
    def test_08(self):
        def fake_fetch_discovery(x):
            # 3
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.57/16",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:0f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:a4:32:b5",
                        "uuid": "7faef191-44d2-4dd9-9492-63b8cce55eae"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.83/16",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:a4:32:b5"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c2",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a4c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.70/16",
                            "ipv4": "172.20.0.70",
                            "mac": "52:54:00:c3:22:c2",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c2"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                }
            ]

        marker = "unit-%s-" % TestSchedulerK8sNode.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_cp = scheduler.K8sControlPlaneScheduler(
            etcd_member_instance=sch_member,
            ignition_control_plane="%sk8s-control-plane" % marker,
            apply_first=True
        )
        sch_cp.fetch_discovery = fake_fetch_discovery
        self.assertEqual(len(sch_cp.etcd_initial_cluster.split(",")), 3)
        self.assertFalse(sch_cp.apply())
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 1)
        groups = self.get_groups()
        self.assertEqual(len(groups), 3)

        def fake_fetch_discovery(x):
            # 7
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.57/16",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:0f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:a4:32:b5",
                        "uuid": "7faef191-44d2-4dd9-9492-63b8cce55eae"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.83/16",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:a4:32:b5"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c2",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a4c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.70/16",
                            "ipv4": "172.20.0.70",
                            "mac": "52:54:00:c3:22:c2",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c2"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c4",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a8c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.100/16",
                            "ipv4": "172.20.0.100",
                            "mac": "52:54:00:c3:22:c4",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c4"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:4f",
                        "uuid": "70fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.101/16",
                            "ipv4": "172.20.0.101",
                            "mac": "52:54:00:95:24:4f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:4f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:5f",
                        "uuid": "67fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.105/16",
                            "ipv4": "172.20.0.105",
                            "mac": "52:54:00:95:24:5f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:5f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:01:95:24:5f",
                        "uuid": "87fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.106/16",
                            "ipv4": "172.20.0.106",
                            "mac": "52:54:01:95:24:5f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:01:95:24:5f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                }
            ]

        sch_cp.fetch_discovery = fake_fetch_discovery
        self.assertTrue(sch_cp.apply())
        self.assertTrue(sch_cp.apply())
        self.assertEqual(len(sch_member.done_list), 3)
        self.assertEqual(len(sch_cp.done_list), 3)
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 2)
        groups = self.get_groups()
        self.assertEqual(len(groups), 6)

        sch_no = scheduler.K8sNodeScheduler(
            k8s_control_plane=sch_cp,
            ignition_node="%sk8s-node" % marker
        )
        sch_no.fetch_discovery = fake_fetch_discovery
        self.assertEqual(len(sch_no.wide_done_list), 6)
        sch_no.apply()
        self.assertEqual(len(sch_no.wide_done_list), 7)

    # @unittest.skip("skip")
    def test_09(self):
        def fake_fetch_discovery(x):
            # 3
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.57/16",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:0f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:a4:32:b5",
                        "uuid": "7faef191-44d2-4dd9-9492-63b8cce55eae"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.83/16",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:a4:32:b5"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c2",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a4c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.70/16",
                            "ipv4": "172.20.0.70",
                            "mac": "52:54:00:c3:22:c2",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c2"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                }
            ]

        marker = "unit-%s-" % TestSchedulerK8sNode.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_cp = scheduler.K8sControlPlaneScheduler(
            etcd_member_instance=sch_member,
            ignition_control_plane="%sk8s-control-plane" % marker,
            apply_first=True
        )
        sch_cp.fetch_discovery = fake_fetch_discovery
        self.assertEqual(len(sch_cp.etcd_initial_cluster.split(",")), 3)
        self.assertFalse(sch_cp.apply())
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 1)
        groups = self.get_groups()
        self.assertEqual(len(groups), 3)

        def fake_fetch_discovery(x):
            # 7
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.57/16",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:0f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:a4:32:b5",
                        "uuid": "7faef191-44d2-4dd9-9492-63b8cce55eae"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.83/16",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:a4:32:b5"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c2",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a4c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.70/16",
                            "ipv4": "172.20.0.70",
                            "mac": "52:54:00:c3:22:c2",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c2"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c4",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a8c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.100/16",
                            "ipv4": "172.20.0.100",
                            "mac": "52:54:00:c3:22:c4",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c4"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:4f",
                        "uuid": "70fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.101/16",
                            "ipv4": "172.20.0.101",
                            "mac": "52:54:00:95:24:4f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:4f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:5f",
                        "uuid": "67fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.105/16",
                            "ipv4": "172.20.0.105",
                            "mac": "52:54:00:95:24:5f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:5f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:01:95:24:5f",
                        "uuid": "87fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.106/16",
                            "ipv4": "172.20.0.106",
                            "mac": "52:54:01:95:24:5f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:01:95:24:5f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                }
            ]

        sch_cp.fetch_discovery = fake_fetch_discovery
        self.assertTrue(sch_cp.apply())
        self.assertTrue(sch_cp.apply())
        self.assertEqual(len(sch_member.done_list), 3)
        self.assertEqual(len(sch_cp.done_list), 3)
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 2)
        groups = self.get_groups()
        self.assertEqual(len(groups), 6)

        sch_no = scheduler.K8sNodeScheduler(
            k8s_control_plane=sch_cp,
            ignition_node="%sk8s-node" % marker
        )
        sch_no.fetch_discovery = fake_fetch_discovery
        self.assertEqual(len(sch_no.wide_done_list), 6)
        self.assertEqual(sch_no.apply(), 1)
        self.assertEqual(len(sch_no.wide_done_list), 7)

        def fake_fetch_discovery(x):
            # 8
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.57/16",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:0f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:a4:32:b5",
                        "uuid": "7faef191-44d2-4dd9-9492-63b8cce55eae"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.83/16",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:a4:32:b5"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c2",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a4c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.70/16",
                            "ipv4": "172.20.0.70",
                            "mac": "52:54:00:c3:22:c2",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c2"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c4",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a8c"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.100/16",
                            "ipv4": "172.20.0.100",
                            "mac": "52:54:00:c3:22:c4",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:c3:22:c4"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:4f",
                        "uuid": "70fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.101/16",
                            "ipv4": "172.20.0.101",
                            "mac": "52:54:00:95:24:4f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:4f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:5f",
                        "uuid": "67fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.105/16",
                            "ipv4": "172.20.0.105",
                            "mac": "52:54:00:95:24:5f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:00:95:24:5f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:54:01:95:24:5f",
                        "uuid": "87fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.106/16",
                            "ipv4": "172.20.0.106",
                            "mac": "52:54:01:95:24:5f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:01:95:24:5f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                },
                {
                    "boot-info": {
                        "mac": "52:11:02:97:24:5f",
                        "uuid": "99fae99f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "cidrv4": "127.0.0.1/8",
                            "ipv4": "127.0.0.1",
                            "mac": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "cidrv4": "172.20.0.250/16",
                            "ipv4": "172.20.0.250",
                            "mac": "52:11:02:97:24:5f",
                            "name": "eth0",
                            "netmask": 21, "gateway": "172.20.0.1"}
                    ],
                    "lldp": {
                        "data": {
                            "interfaces": [
                                {
                                    "chassis": {
                                        "id": "28:f1:0e:12:20:00",
                                        "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                                    },
                                    "port": {
                                        "id": "fe:54:01:95:24:5f"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                }
            ]

        sch_no.fetch_discovery = fake_fetch_discovery
        self.assertEqual(sch_no.apply(), 2)
        self.assertEqual(len(sch_no.wide_done_list), 8)
        self.assertEqual(sch_no.apply(), 2)
        self.assertEqual(len(sch_no.wide_done_list), 8)
