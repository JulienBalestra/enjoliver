import os
import sys
import unittest

from flask import Flask, request

from app import generator

try:
    import kvm_player
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import kvm_player


@unittest.skipIf(os.getenv("KVM_ISO", None) is None, "TestKVMBasicISO need env KVM_ISO=whatever")
class TestKVMBasicISO(kvm_player.KernelVirtualMachinePlayer):
    flask_ok_port = 5050

    @classmethod
    def setUpClass(cls):
        cls.check_requirements()
        cls.set_rack0()
        cls.set_matchbox()
        cls.set_dnsmasq()
        cls.set_api()
        cls.pause(cls.wait_setup_teardown)

    def test_00(self):
        marker = "euid-%s-%s" % (TestKVMBasicISO.__name__.lower(), self.test_00.__name__)
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            matchbox_path=self.test_matchbox_path
        )
        gen.dumps()

        app = Flask(marker)
        resp = []

        @app.route('/ok', methods=['POST'])
        def machine_ready():
            resp.append(request.form.keys())
            request.environ.get('werkzeug.server.shutdown')()
            return "roger\n"

        destroy, undefine = ["virsh", "destroy", "%s" % marker], ["virsh", "undefine", "%s" % marker]
        self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)

        try:
            virt_install = [
                "virt-install",
                "--name",
                "%s" % marker,
                "--network=bridge:rack0,model=virtio",
                "--memory=1024",
                "--vcpus=%d" % self.get_optimized_cpu(1),
                "--cdrom",
                "%s/ipxe.iso" % self.tests_path,
                "--disk",
                "none",
                "--os-type=linux",
                "--os-variant=generic",
                "--noautoconsole",
                "--boot=cdrom"
            ]
            self.virsh(virt_install, assertion=True, v=self.dev_null)

            app.run(
                host="172.20.0.1", port=self.flask_ok_port, debug=False, use_reloader=False)

        finally:
            self.virsh(destroy)
            self.virsh(undefine)
        self.assertItemsEqual(resp, [['euid-testkvmbasiciso-test_00']])

    # @unittest.skip("just skip")
    def test_01(self):
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMBasicISO.__name__.lower(), self.test_01.__name__)
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            matchbox_path=self.test_matchbox_path
        )
        gen.dumps()

        app = Flask(marker)
        resp = []

        @app.route('/ok', methods=['POST'])
        def machine_ready():
            resp.append(request.form.keys())
            if len(resp) == nb_node:
                request.environ.get('werkzeug.server.shutdown')()
            return "roger\n"

        try:
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % machine_marker,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=1024",
                    "--vcpus=%d" % self.get_optimized_cpu(nb_node),
                    "--cdrom",
                    "%s/ipxe.iso" % self.tests_path,
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=cdrom"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)

            app.run(
                host="172.20.0.1", port=self.flask_ok_port, debug=False, use_reloader=False)

        finally:
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy)
                self.virsh(undefine)
        self.assertEqual(nb_node, len(resp))
        self.assertItemsEqual(resp, [
            ['euid-testkvmbasiciso-test_01'],
            ['euid-testkvmbasiciso-test_01'],
            ['euid-testkvmbasiciso-test_01']])

    # @unittest.skip("just skip")
    def test_02(self):
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMBasicISO.__name__.lower(), self.test_02.__name__)

        app = Flask(marker)
        resp = []

        @app.route('/ok', methods=['POST'])
        def machine_ready():
            resp.append(request.form.keys())
            if len(resp) == nb_node:
                request.environ.get('werkzeug.server.shutdown')()
            return "roger\n"

        base_mac = "52:54:00:78:83:0"
        try:
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                gen = generator.Generator(
                    api_uri=self.api_uri,
                    profile_id="%s" % machine_marker,
                    name="%s" % machine_marker,
                    ignition_id="%s.yaml" % machine_marker,
                    matchbox_path=self.test_matchbox_path,
                    selector={"mac": "%s%d" % (base_mac, i)}
                )
                gen.dumps()
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % machine_marker,
                    "--network=bridge:rack0,model=virtio,mac=%s%d" % (base_mac, i),
                    "--memory=1024",
                    "--vcpus=%d" % self.get_optimized_cpu(nb_node),
                    "--cdrom",
                    "%s/ipxe.iso" % self.tests_path,
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=cdrom"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)

            app.run(
                host="172.20.0.1", port=self.flask_ok_port, debug=False, use_reloader=False)
        finally:
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy, v=self.dev_null)
                self.virsh(undefine, v=self.dev_null)
        self.assertEqual(nb_node, len(resp))
        self.assertItemsEqual(resp, [
            ['euid-testkvmbasiciso-test_02-0'],
            ['euid-testkvmbasiciso-test_02-2'],
            ['euid-testkvmbasiciso-test_02-1']])


if __name__ == "__main__":
    unittest.main()
