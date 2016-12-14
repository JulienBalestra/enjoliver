import json
import os
import subprocess
import unittest

from app import scheduler


class TestEtcdSchedulerMember(unittest.TestCase):
    __name__ = "TestEtcdScheduler"
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    app_path = "%s" % os.path.split(tests_path)[0]
    project_path = "%s" % os.path.split(app_path)[0]
    test_bootcfg_path = "%s/test_bootcfg" % tests_path

    @classmethod
    def setUpClass(cls):
        subprocess.check_output(["make", "-C", cls.project_path])
        os.environ["BOOTCFG_URI"] = "http://127.0.0.1:8080"
        os.environ["API_URI"] = "http://127.0.0.1:5000"

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (TestEtcdSchedulerMember.test_bootcfg_path, k)
                for k in ("profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.write(1, "\r-> remove %s\n\r" % f)
                    os.remove("%s/%s" % (d, f))

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
                    "cidrv4": "172.20.0.57/21",
                    "ipv4": "172.20.0.57",
                    "mac": "52:54:00:95:24:0f",
                    "name": "eth0",
                    "netmask": 21
                }
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
        ret = scheduler.EtcdMemberScheduler.get_machine_boot_ip_mac(m)
        self.assertEqual(ret, ("172.20.0.57", "52:54:00:95:24:0f"))

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
                    "cidrv4": "172.20.0.57/21",
                    "ipv4": "172.20.0.57",
                    "mac": "52:54:00:95:24:0f",
                    "name": "eth0",
                    "netmask": 21
                }
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
            scheduler.EtcdMemberScheduler.get_machine_boot_ip_mac(m)

    # @unittest.skip("skip")
    def test_00(self):
        def fake_fetch_discovery(x, y):
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
                            "cidrv4": "172.20.0.57/21",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21
                        }
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
                            "cidrv4": "172.20.0.83/21",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21
                        }
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
                            "cidrv4": "172.20.0.70/21",
                            "ipv4": "172.20.0.70",
                            "mac": "52:54:00:c3:22:c2",
                            "name": "eth0",
                            "netmask": 21
                        }
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

        marker = "unit-%s-" % (TestEtcdSchedulerMember.__name__.lower())
        scheduler.CommonScheduler.fetch_discovery = fake_fetch_discovery
        sch = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        self.assertTrue(sch.apply())
        etcd_groups = []
        for i in xrange(sch.etcd_members_nb):
            with open("%s/groups/%semember-%d.json" % (
                    self.test_bootcfg_path, marker, i)) as group:
                etcd_groups.append(json.loads(group.read()))
        self.assertEqual(3, len(etcd_groups))

        ref = 0
        for g in etcd_groups:
            ref += 1
            self.assertEqual(len(g["metadata"]["etcd_initial_cluster"].split(",")), 3)
            self.assertEqual(g["metadata"]["etcd_initial_cluster"],
                             "static0=http://172.20.0.70:2380,"
                             "static1=http://172.20.0.83:2380,"
                             "static2=http://172.20.0.57:2380")
        self.assertTrue(ref == 3)

        etcd_profile = "%s/profiles/%semember.json" % (self.test_bootcfg_path, marker)
        with open(etcd_profile) as p:
            p_data = json.loads(p.read())
        self.assertEqual(p_data["ignition_id"],
                         "unit-testetcdschedulermember-emember.yaml")

    # @unittest.skip("skip")
    def test_01(self):
        def fake_fetch_discovery(y):
            return [
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
                            "cidrv4": "172.20.0.83/21",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21
                        }
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
                }
            ]

        marker = "unit-%s-%s-" % (TestEtcdSchedulerMember.__name__.lower(), self.test_01.__name__)
        sch = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch.fetch_discovery = fake_fetch_discovery
        self.assertFalse(sch.apply())

        etcd_groups = []
        for i in xrange(sch.etcd_members_nb):
            with self.assertRaises(IOError):
                with open("%s/groups/%semember-%d.json" % (
                        self.test_bootcfg_path, marker, i)) as group:
                    etcd_groups.append(json.loads(group.read()))
        self.assertEqual(0, len(etcd_groups))

    # @unittest.skip("skip")
    def test_02(self):
        def fake_fetch_discovery(x):
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
                            "cidrv4": "172.20.0.57/21",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21
                        }
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
                            "cidrv4": "172.20.0.83/21",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21
                        }
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
                }
            ]

        marker = "unit-%s-%s-" % (TestEtcdSchedulerMember.__name__.lower(), self.test_01.__name__)
        sch = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch.fetch_discovery = fake_fetch_discovery
        self.assertFalse(sch.apply())

        etcd_groups = []
        for i in xrange(sch.etcd_members_nb):
            with self.assertRaises(IOError):
                with open("%s/groups/%semember-%d.json" % (
                        self.test_bootcfg_path, marker, i)) as group:
                    etcd_groups.append(json.loads(group.read()))
        self.assertEqual(0, len(etcd_groups))

    # @unittest.skip("skip")
    def test_03(self):
        def fake_fetch_discovery(x):
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
                            "cidrv4": "172.20.0.57/21",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21
                        }
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
                            "cidrv4": "172.20.0.83/21",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21
                        }
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
                            "cidrv4": "172.20.0.70/21",
                            "ipv4": "172.20.0.70",
                            "mac": "52:54:00:c3:22:c2",
                            "name": "eth0",
                            "netmask": 21
                        }
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

        marker = "unit-%s-" % (TestEtcdSchedulerMember.__name__.lower())
        sch = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch.fetch_discovery = fake_fetch_discovery
        self.assertTrue(sch.apply())
        etcd_groups = []
        for i in xrange(sch.etcd_members_nb):
            with open("%s/groups/%semember-%d.json" % (
                    self.test_bootcfg_path, marker, i)) as group:
                etcd_groups.append(json.loads(group.read()))
        self.assertEqual(3, len(etcd_groups))

        self.assertEqual(3, len(etcd_groups))

        ref = 0
        for g in etcd_groups:
            ref += 1
            self.assertEqual(len(g["metadata"]["etcd_initial_cluster"].split(",")), 3)
            self.assertEqual(g["metadata"]["etcd_initial_cluster"],
                             "static0=http://172.20.0.70:2380,"
                             "static1=http://172.20.0.83:2380,"
                             "static2=http://172.20.0.57:2380")
        self.assertTrue(ref == 3)

        etcd_profile = "%s/profiles/%semember.json" % (self.test_bootcfg_path, marker)
        with open(etcd_profile) as p:
            p_data = json.loads(p.read())
        self.assertEqual(p_data["ignition_id"],
                         "unit-testetcdschedulermember-emember.yaml")
        self.assertTrue(sch.apply())

        self.assertEqual(3, len(etcd_groups))

        ref = 0
        for g in etcd_groups:
            ref += 1
            self.assertEqual(len(g["metadata"]["etcd_initial_cluster"].split(",")), 3)
            self.assertEqual(g["metadata"]["etcd_initial_cluster"],
                             "static0=http://172.20.0.70:2380,"
                             "static1=http://172.20.0.83:2380,"
                             "static2=http://172.20.0.57:2380")
        self.assertTrue(ref == 3)

    # @unittest.skip("skip")
    def test_04(self):
        def fake_fetch_discovery(x, y):
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
                            "cidrv4": "172.20.0.57/21",
                            "ipv4": "172.20.0.57",
                            "mac": "52:54:00:95:24:0f",
                            "name": "eth0",
                            "netmask": 21
                        }
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
                            "cidrv4": "172.20.0.83/21",
                            "ipv4": "172.20.0.83",
                            "mac": "52:54:00:a4:32:b5",
                            "name": "eth0",
                            "netmask": 21
                        }
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
                }
            ]

        marker = "unit-%s-" % (TestEtcdSchedulerMember.__name__.lower())
        scheduler.EtcdMemberScheduler.fetch_discovery = fake_fetch_discovery
        sch = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        self.assertFalse(sch.apply())
        sch.fetch_discovery = lambda x: [
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
                        "cidrv4": "172.20.0.57/21",
                        "ipv4": "172.20.0.57",
                        "mac": "52:54:00:95:24:0f",
                        "name": "eth0",
                        "netmask": 21
                    }
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
                        "cidrv4": "172.20.0.83/21",
                        "ipv4": "172.20.0.83",
                        "mac": "52:54:00:a4:32:b5",
                        "name": "eth0",
                        "netmask": 21
                    }
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
                        "cidrv4": "172.20.0.70/21",
                        "ipv4": "172.20.0.70",
                        "mac": "52:54:00:c3:22:c2",
                        "name": "eth0",
                        "netmask": 21
                    }
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
        self.assertTrue(sch.apply())
        etcd_groups = []
        for i in xrange(sch.etcd_members_nb):
            with open("%s/groups/%semember-%d.json" % (
                    self.test_bootcfg_path, marker, i)) as group:
                etcd_groups.append(json.loads(group.read()))
        self.assertEqual(3, len(etcd_groups))

        self.assertEqual(3, len(etcd_groups))

        ref = 0
        for g in etcd_groups:
            ref += 1
            self.assertEqual(len(g["metadata"]["etcd_initial_cluster"].split(",")), 3)
            self.assertEqual(g["metadata"]["etcd_initial_cluster"],
                             "static0=http://172.20.0.70:2380,"
                             "static1=http://172.20.0.83:2380,"
                             "static2=http://172.20.0.57:2380")
        self.assertTrue(ref == 3)

        etcd_profile = "%s/profiles/%semember.json" % (self.test_bootcfg_path, marker)
        with open(etcd_profile) as p:
            p_data = json.loads(p.read())
        self.assertEqual(p_data["ignition_id"],
                         "unit-testetcdschedulermember-emember.yaml")
        self.assertTrue(sch.apply())

        self.assertEqual(3, len(etcd_groups))

        ref = 0
        for g in etcd_groups:
            ref += 1
            self.assertEqual(len(g["metadata"]["etcd_initial_cluster"].split(",")), 3)
            self.assertEqual(g["metadata"]["etcd_initial_cluster"],
                             "static0=http://172.20.0.70:2380,"
                             "static1=http://172.20.0.83:2380,"
                             "static2=http://172.20.0.57:2380")
        self.assertTrue(ref == 3)

    # @unittest.skip("skip")
    def test_05(self):
        def fake_fetch_discovery(x, y):
            return None

        marker = "unit-%s-%s-" % (TestEtcdSchedulerMember.__name__.lower(), self.test_00.__name__)
        scheduler.EtcdMemberScheduler.fetch_discovery = fake_fetch_discovery
        sch = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        self.assertFalse(sch.apply())
