import os
import sys
import time
import unittest

from flask import Flask, request

from app import generator

try:
    import kvm_player
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import kvm_player


@unittest.skipIf(os.getenv("KVM_PXE", None) is None, "TestKVMBasicPXE need env KVM_PXE=whatever")
class TestKVMBasicPXE(kvm_player.KernelVirtualMachinePlayer):
    flask_ok_port = 5050

    @classmethod
    def setUpClass(cls):
        cls.check_requirements()
        cls.set_rack0()
        cls.set_matchbox()
        cls.set_dnsmasq()
        cls.set_api()
        cls.pause(cls.wait_setup_teardown)

    # @unittest.skip("just skip")
    def test_00(self):
        marker = "euid-%s-%s" % (TestKVMBasicPXE.__name__.lower(), self.test_00.__name__)
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
                "--vcpus=%d" % self.get_optimized_cpu(nb_node),
                "--pxe",
                "--disk",
                "none",
                "--os-type=linux",
                "--os-variant=generic",
                "--noautoconsole",
                "--boot=network"
            ]
            self.virsh(virt_install, assertion=True, v=self.dev_null)

            app.run(
                host="172.20.0.1", port=self.flask_ok_port, debug=False, use_reloader=False)

        finally:
            self.virsh(destroy)
            self.virsh(undefine)
        self.assertItemsEqual(resp, [['euid-testkvmbasicpxe-test_00']])

    # @unittest.skip("just skip")
    def test_01(self):
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMBasicPXE.__name__.lower(), self.test_01.__name__)
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
                    "--pxe",
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=network"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.testing_sleep_seconds)

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
            ['euid-testkvmbasicpxe-test_01'],
            ['euid-testkvmbasicpxe-test_01'],
            ['euid-testkvmbasicpxe-test_01']])


if __name__ == "__main__":
    unittest.main()
