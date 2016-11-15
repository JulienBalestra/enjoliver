import json
import os
import subprocess
import unittest

from app import scheduler


class TestEtcdSchedulerProxy(unittest.TestCase):
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
        dirs = ["%s/%s" % (TestEtcdSchedulerProxy.test_bootcfg_path, k)
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
                    "CIDRv4": "127.0.0.1/8",
                    "IPv4": "127.0.0.1",
                    "MAC": "",
                    "name": "lo",
                    "netmask": 8
                },
                {
                    "CIDRv4": "172.20.0.57/21",
                    "IPv4": "172.20.0.57",
                    "MAC": "52:54:00:95:24:0f",
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
                    "CIDRv4": "127.0.0.1/8",
                    "IPv4": "127.0.0.1",
                    "MAC": "",
                    "name": "lo",
                    "netmask": 8
                },
                {
                    "CIDRv4": "172.20.0.57/21",
                    "IPv4": "172.20.0.57",
                    "MAC": "52:54:00:95:24:0f",
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
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.57/21",
                            "IPv4": "172.20.0.57",
                            "MAC": "52:54:00:95:24:0f",
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
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.83/21",
                            "IPv4": "172.20.0.83",
                            "MAC": "52:54:00:a4:32:b5",
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
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.70/21",
                            "IPv4": "172.20.0.70",
                            "MAC": "52:54:00:c3:22:c2",
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

        marker = "unit-%s-" % TestEtcdSchedulerProxy.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        self.assertTrue(sch_member.apply())
        sch_proxy = scheduler.EtcdProxyScheduler(
            etcd_member_instance=sch_member,
            ignition_proxy="%seproxy" % marker
        )
        self.assertEqual(sch_proxy.etcd_initial_cluster,
                         "static0=http://172.20.0.70:2380,"
                         "static1=http://172.20.0.83:2380,"
                         "static2=http://172.20.0.57:2380")

    # @unittest.skip("skip")
    def test_04(self):
        def fake_fetch_discovery(x):
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.57/21",
                            "IPv4": "172.20.0.57",
                            "MAC": "52:54:00:95:24:0f",
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
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.83/21",
                            "IPv4": "172.20.0.83",
                            "MAC": "52:54:00:a4:32:b5",
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
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.70/21",
                            "IPv4": "172.20.0.70",
                            "MAC": "52:54:00:c3:22:c2",
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

        marker = "unit-%s-" % TestEtcdSchedulerProxy.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_proxy = scheduler.EtcdProxyScheduler(
            etcd_member_instance=sch_member,
            ignition_proxy="%seproxy" % marker,
            apply_first=True
        )
        self.assertEqual(sch_proxy.etcd_initial_cluster,
                         "static0=http://172.20.0.70:2380,"
                         "static1=http://172.20.0.83:2380,"
                         "static2=http://172.20.0.57:2380")

    # @unittest.skip("skip")
    def test_05(self):
        def fake_fetch_discovery(x):
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.57/21",
                            "IPv4": "172.20.0.57",
                            "MAC": "52:54:00:95:24:0f",
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
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.83/21",
                            "IPv4": "172.20.0.83",
                            "MAC": "52:54:00:a4:32:b5",
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
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.70/21",
                            "IPv4": "172.20.0.70",
                            "MAC": "52:54:00:c3:22:c2",
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

        marker = "unit-%s-" % TestEtcdSchedulerProxy.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_proxy = scheduler.EtcdProxyScheduler(
            etcd_member_instance=sch_member,
            ignition_proxy="%seproxy" % marker
        )
        sch_proxy.fetch_discovery = fake_fetch_discovery
        self.assertEqual(sch_proxy.etcd_initial_cluster, None)
        sch_proxy.apply_member()
        self.assertEqual(sch_proxy.etcd_initial_cluster,
                         "static0=http://172.20.0.70:2380,"
                         "static1=http://172.20.0.83:2380,"
                         "static2=http://172.20.0.57:2380")

    # @unittest.skip("skip")
    def test_06(self):
        def fake_fetch_discovery(x):
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.57/21",
                            "IPv4": "172.20.0.57",
                            "MAC": "52:54:00:95:24:0f",
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
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.83/21",
                            "IPv4": "172.20.0.83",
                            "MAC": "52:54:00:a4:32:b5",
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
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.70/21",
                            "IPv4": "172.20.0.70",
                            "MAC": "52:54:00:c3:22:c2",
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

        marker = "unit-%s-" % TestEtcdSchedulerProxy.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_proxy = scheduler.EtcdProxyScheduler(
            etcd_member_instance=sch_member,
            ignition_proxy="%seproxy" % marker,
            apply_first=True
        )
        sch_proxy.fetch_discovery = fake_fetch_discovery
        self.assertEqual(sch_proxy.etcd_initial_cluster,
                         "static0=http://172.20.0.70:2380,"
                         "static1=http://172.20.0.83:2380,"
                         "static2=http://172.20.0.57:2380")
        self.assertEqual(sch_proxy.apply(), 0)

    # @unittest.skip("skip")
    def test_07(self):
        def fake_fetch_discovery(x):
            return [
                {
                    "boot-info": {
                        "mac": "52:54:00:95:24:0f",
                        "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
                    },
                    "interfaces": [
                        {
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.57/21",
                            "IPv4": "172.20.0.57",
                            "MAC": "52:54:00:95:24:0f",
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
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.83/21",
                            "IPv4": "172.20.0.83",
                            "MAC": "52:54:00:a4:32:b5",
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
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.70/21",
                            "IPv4": "172.20.0.70",
                            "MAC": "52:54:00:c3:22:c2",
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
                },
                {
                    "boot-info": {
                        "mac": "52:54:00:c3:22:c4",
                        "uuid": "40cab2a6-62eb-4fb3-b798-5aca4c6f3a8c"
                    },
                    "interfaces": [
                        {
                            "CIDRv4": "127.0.0.1/8",
                            "IPv4": "127.0.0.1",
                            "MAC": "",
                            "name": "lo",
                            "netmask": 8
                        },
                        {
                            "CIDRv4": "172.20.0.70/21",
                            "IPv4": "172.20.0.70",
                            "MAC": "52:54:00:c3:22:c4",
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
                                        "id": "fe:54:00:c3:22:c4"
                                    }
                                }
                            ]
                        },
                        "is_file": True
                    }
                }
            ]

        marker = "unit-%s-" % TestEtcdSchedulerProxy.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_proxy = scheduler.EtcdProxyScheduler(
            etcd_member_instance=sch_member,
            ignition_proxy="%seproxy" % marker,
            apply_first=True
        )
        sch_proxy.fetch_discovery = fake_fetch_discovery
        self.assertEqual(sch_proxy.etcd_initial_cluster,
                         "static0=http://172.20.0.70:2380,"
                         "static1=http://172.20.0.83:2380,"
                         "static2=http://172.20.0.57:2380")
        self.assertEqual(sch_proxy.apply(), 1)
