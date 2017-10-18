import datetime
import json
import multiprocessing
import os
import re
import shutil
import socket
import subprocess
import unittest
import warnings

import requests
import sys
import time
import yaml
from kubernetes import client as kubeclient

from app import generator, configs


def is_virtinstall():
    with open("/dev/null", "w") as f:
        virtinstall = 2
        try:
            virtinstall = subprocess.call(
                ["virt-install", "--version"], stdout=f, stderr=f)
        except OSError:
            pass
    return virtinstall


def get_kvm_sleep(f="/tmp/virt-host-validate"):
    d = 3
    try:
        with open(f, 'w') as w:
            subprocess.call(["virt-host-validate", "qemu"], stdout=w)
            with open(f, 'r') as r:
                for l in r.readlines():
                    if "QEMU: Checking for hardware virtualization" in l:
                        if "PASS" not in l:
                            d *= 2
                        break
                r.seek(0)
                display(r.read())
        os.remove(f)
    except OSError:
        pass
    return d


def display(message):
    for i in range(5):
        try:
            print(message)
            return
        except BlockingIOError:
            time.sleep(0.01)


@unittest.skipIf(os.geteuid() != 0, "TestKVMDiscovery need privilege")
@unittest.skipIf(is_virtinstall() != 0, "TestKVMDiscovery need virt-install")
class KernelVirtualMachinePlayer(unittest.TestCase):
    """
    This class is used by all Kernel Virtual Machine testing suite
    Override the setUpClass by selecting your custom environment with the following catalog:
    >>> @classmethod
    >>> def setUpClass(cls):
    >>>     cls.running_requirements()
    >>>     cls.set_acserver()
    >>>     cls.set_api()
    >>>     cls.set_matchbox()
    >>>     cls.set_dnsmasq()
    >>>     cls.set_lldp()
    >>>     cls.set_rack0()
    >>>     cls.pause(cls.wait_setup_teardown)
    Note: you may use 'reset -q' because of Link Layer Discovery Protocol Container's
    """
    __name__ = "KernelVirtualMachinePlayer"

    p_matchbox = multiprocessing.Process
    p_dnsmasq = multiprocessing.Process
    p_api = multiprocessing.Process
    p_lldp = multiprocessing.Process
    p_list = []
    gen = generator.Generator

    euid_path = "%s" % os.path.dirname(os.path.abspath(__file__))
    tests_path = "%s" % os.path.dirname(euid_path)
    app_path = os.path.dirname(tests_path)
    project_path = os.path.dirname(app_path)
    matchbox_path = "%s/matchbox" % project_path
    assets_path = "%s/matchbox/assets" % project_path

    runtime_path = "%s/runtime" % project_path
    rkt_bin = "%s/rkt/rkt" % runtime_path
    helm_bin = "%s/helm/helm" % runtime_path
    matchbox_bin = "%s/matchbox/matchbox" % runtime_path
    acserver_bin = "%s/run_acserver.py" % runtime_path

    ssh_private_key = os.path.join(tests_path, "testing.id_rsa")
    test_certs_path = "%s/test_certs" % tests_path
    test_matchbox_path = "%s/test_matchbox" % tests_path

    matchbox_port = int(os.getenv("MATCHBOX_PORT", "8080"))

    api_port = int(os.getenv("API_PORT", "5000"))

    api_ip = "172.20.0.1"
    api_uri = "http://%s:%d" % (api_ip, api_port)

    dev_null = open("/dev/null", "w")

    testing_sleep_seconds = get_kvm_sleep()
    wait_setup_teardown = 3

    os.environ["ENJOLIVER_API_URI"] = api_uri
    os.environ["ENJOLIVER_MATCHBOX_PATH"] = test_matchbox_path
    os.environ["ENJOLIVER_MATCHBOX_ASSETS"] = assets_path
    os.environ["ENJOLIVER_KUBERNETES_APISERVER_INSECURE_BIND_ADDRESS"] = "0.0.0.0"
    ec = configs.EnjoliverConfig(importer=__file__)

    # Memory needed for RAM nodes
    ram_kvm_node_memory_mb = 9216

    @staticmethod
    def pause(t=600):
        """
        Sleep for eventual side testing or tests/s.sh ...
        :param t: 10 minutes
        :return: None
        """
        try:
            display("==> sleep %d..." % t)
            time.sleep(t)
        except KeyboardInterrupt:
            pass
        finally:
            display("==> sleep finish")

    @staticmethod
    def process_target_matchbox():
        os.environ["MATCHBOX_PATH"] = KernelVirtualMachinePlayer.test_matchbox_path
        cmd = [
            "%s" % sys.executable,
            "%s/manage.py" % KernelVirtualMachinePlayer.project_path,
            "matchbox",
        ]
        display("PID  -> %s\n"
                "exec -> %s" % (os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.environ["TERM"] = "xterm"
        os.execve(cmd[0], cmd, os.environ)

    @staticmethod
    def process_target_acserver():
        cmd = [
            "%s" % KernelVirtualMachinePlayer.acserver_bin,
        ]
        display("PID  -> %s\n"
                "exec -> %s" % (os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.environ["TERM"] = "xterm"
        os.execve(cmd[0], cmd, os.environ)

    @staticmethod
    def process_target_api():
        os.environ["ENJOLIVER_DB_PATH"] = "%s/enjoliver.sqlite" % KernelVirtualMachinePlayer.euid_path
        os.environ["ENJOLIVER_IGNITION_JOURNAL_DIR"] = "%s/ignition_journal" % KernelVirtualMachinePlayer.euid_path

        try:
            os.remove(os.environ["ENJOLIVER_DB_PATH"])
        except OSError:
            pass

        shutil.rmtree(os.environ["ENJOLIVER_IGNITION_JOURNAL_DIR"], ignore_errors=True)

        try:
            with open("%s/.config/enjoliver/config.json" % os.getenv("HOME")) as f:
                conf = json.load(f)
                os.environ["ENJOLIVER_AWS_ACCESS_KEY_ID"] = conf["AWS_ACCESS_KEY_ID"]
                os.environ["ENJOLIVER_AWS_SECRET_ACCESS_KEY"] = conf["AWS_SECRET_ACCESS_KEY"]
        except (IOError, ValueError):
            pass

        os.environ["ENJOLIVER_BACKUP_BUCKET_NAME"] = "bbcenjoliver-dev"
        os.environ["ENJOLIVER_SYNC_NOTIFY_TTL"] = "0"
        cmd = [
            "%s" % sys.executable,
            "%s/manage.py" % KernelVirtualMachinePlayer.project_path,
            "gunicorn",
        ]
        display("PID  -> %s\n"
                "exec -> %s" % (os.getpid(), " ".join(cmd)))
        os.execve(cmd[0], cmd, os.environ)

    @staticmethod
    def process_target_dnsmasq():
        cmd = [
            "%s" % KernelVirtualMachinePlayer.rkt_bin,
            "--local-config=%s" % KernelVirtualMachinePlayer.tests_path,
            "--mount",
            "volume=config,target=/etc/dnsmasq.conf",
            "--mount",
            "volume=resolv,target=/etc/resolv.conf",
            "run",
            "enjoliver.local/dnsmasq:latest",
            "--insecure-options=all",
            "--net=host",
            "--interactive",
            "--caps-retain=all",
            "--set-env=TERM=%s" % os.getenv("TERM", "xterm"),
            "--uuid-file-save=/tmp/dnsmasq.uuid",
            "--volume",
            "resolv,kind=host,source=/etc/resolv.conf",
            "--volume",
            "config,kind=host,source=%s/dnsmasq-rack0.conf" % KernelVirtualMachinePlayer.tests_path
        ]
        display("PID  -> %s\n"
                "exec -> %s" % (os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execve(cmd[0], cmd, os.environ)
        os._exit(2)

    @staticmethod
    def fetch_lldpd():
        cmd = [
            "%s" % KernelVirtualMachinePlayer.rkt_bin,
            "--local-config=%s" % KernelVirtualMachinePlayer.tests_path,
            "fetch",
            "--insecure-options=all",
            KernelVirtualMachinePlayer.ec.lldp_image_url]
        assert subprocess.call(cmd) == 0

    @staticmethod
    def process_target_lldpd():
        cmd = [
            "%s" % KernelVirtualMachinePlayer.rkt_bin,
            "--local-config=%s" % KernelVirtualMachinePlayer.tests_path,
            "run",
            KernelVirtualMachinePlayer.ec.lldp_image_url,
            "--insecure-options=all",
            "--net=host",
            "--interactive",
            "--set-env=TERM=%s" % os.getenv("TERM", "xterm"),
            "--exec",
            "/usr/sbin/lldpd",
            "--",
            "-dd"]
        display("PID  -> %s\n"
                "exec -> %s" % (os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execve(cmd[0], cmd, os.environ)
        os._exit(2)  # Should not happen

    @staticmethod
    def dns_masq_running():
        display("DNSMASQ probing...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = 1
        for i in range(120):
            result = sock.connect_ex(('172.20.0.1', 53))
            if result == 0:
                break
            time.sleep(0.5)
            if i % 10 == 0:
                display("DNSMASQ still NOT ready")
        sock.close()
        assert result == 0
        display("DNSMASQ ready")
        sys.stdout.flush()

    @staticmethod
    def acserver_is_running():
        url = "http://enjoliver.local"
        for t in range(20):
            try:
                r = requests.get(url)
                r.close()
                return
            except Exception as e:
                display(" GET -> %s : %s" % (url, e))
            time.sleep(0.5)
        r = requests.get(url)
        r.close()

    @classmethod
    def running_requirements(cls):
        warnings.simplefilter("ignore", ResourceWarning)
        # TODO validate the assets in this method
        if os.geteuid() != 0:
            raise RuntimeError("Need to be root EUID == %d" % os.geteuid())

        cls.clean_sandbox()

        if os.path.isfile(KernelVirtualMachinePlayer.rkt_bin) is False or \
                        os.path.isfile(KernelVirtualMachinePlayer.matchbox_bin) is False or \
                        os.path.isfile(KernelVirtualMachinePlayer.acserver_bin) is False:
            display("Call 'make runtime' as user for:\n"
                    "- %s\n" % KernelVirtualMachinePlayer.rkt_bin +
                    "- %s\n" % KernelVirtualMachinePlayer.matchbox_bin +
                    "- %s\n" % KernelVirtualMachinePlayer.acserver_bin)
            exit(2)
        if os.path.isfile(cls.ssh_private_key) is False:
            display("Call 'make testing.id_rsa' as user\n")
            exit(3)

        display("PID -> %s" % os.getpid())

    @classmethod
    def set_matchbox(cls):
        cls.p_matchbox = multiprocessing.Process(target=KernelVirtualMachinePlayer.process_target_matchbox,
                                                 name="matchbox")
        cls.p_matchbox.start()
        time.sleep(0.5)
        assert cls.p_matchbox.is_alive() is True
        cls.p_list.append(cls.p_matchbox)

    @classmethod
    def set_rack0(cls):
        cmd = [
            "%s" % KernelVirtualMachinePlayer.rkt_bin,
            "--local-config=%s" % KernelVirtualMachinePlayer.tests_path,
            "run",
            "--net=rack0",
            "--interactive",
            "--set-env=TERM=%s" % os.getenv("TERM", "xterm"),
            "--insecure-options=all",
            "coreos.com/rkt/stage1-coreos",
            "--exec",
            "/bin/bash", "--", "-c", "exit", "0"]
        display("call %s" % " ".join(cmd))
        ret = subprocess.call(cmd)
        display("Bridge w/ iptables creation exit: %d" % ret)
        assert subprocess.call(["ip", "link", "show", "rack0"]) == 0

    @classmethod
    def set_dnsmasq(cls):
        cls.p_dnsmasq = multiprocessing.Process(target=KernelVirtualMachinePlayer.process_target_dnsmasq,
                                                name="dnsmasq")
        cls.p_dnsmasq.start()
        time.sleep(0.5)
        assert cls.p_dnsmasq.is_alive() is True
        cls.dns_masq_running()
        cls.p_list.append(cls.p_dnsmasq)

    @classmethod
    def set_api(cls):
        cls.p_api = multiprocessing.Process(target=KernelVirtualMachinePlayer.process_target_api, name="api")
        cls.p_api.start()
        time.sleep(0.5)
        assert cls.p_api.is_alive() is True
        cls.p_list.append(cls.p_api)

    @classmethod
    def set_acserver(cls):
        cls.p_acserver = multiprocessing.Process(target=KernelVirtualMachinePlayer.process_target_acserver,
                                                 name="acserver")
        cls.p_acserver.start()
        time.sleep(1)
        if cls.p_acserver.is_alive() is True:
            cls.p_list.append(cls.p_acserver)

    @classmethod
    def set_lldp(cls):
        cls.fetch_lldpd()
        cls.p_lldp = multiprocessing.Process(target=KernelVirtualMachinePlayer.process_target_lldpd, name="lldp")
        cls.p_lldp.start()
        time.sleep(0.5)
        assert cls.p_lldp.is_alive() is True
        cls.p_list.append(cls.p_lldp)

    @classmethod
    def setUpClass(cls):
        raise NotImplementedError

    @classmethod
    def tearDownClass(cls):
        for p in cls.p_list:
            if p.is_alive():
                display("TERM -> %s %s" % (p.pid, p.name))
                p.terminate()
                p.join(10)
                if p.is_alive():
                    os.kill(p.pid, 9)
                display("END -> %s %s" % (p.exitcode, p.name))
            display("EXITED -> %s %s" % (p.exitcode, p.name))

        subprocess.call([
            "%s" % KernelVirtualMachinePlayer.rkt_bin,
            "--local-config=%s" % KernelVirtualMachinePlayer.tests_path,
            "gc",
            "--grace-period=0s"])
        cls.clean_sandbox()
        cls.pause(cls.wait_setup_teardown)
        cls.write_ending(cls.__name__)
        subprocess.check_output(["reset", "-q"])

    @staticmethod
    def write_ending(message):
        with open("/tmp/unittest.end", "a") as f:
            f.write("%s %s" % (datetime.datetime.now(), message))

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (KernelVirtualMachinePlayer.test_matchbox_path, k)
                for k in ("profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    display("-> remove %s" % f)
                    os.remove("%s/%s" % (d, f))
        for f in os.listdir(os.path.join(KernelVirtualMachinePlayer.tests_path, "test_certs")):
            if f != ".gitkeep":
                os.remove(os.path.join(KernelVirtualMachinePlayer.tests_path, "test_certs", f))

    def api_healthz(self, first=True):
        """
        If the api just respond on the route it's fine
        :param first:
        :return:
        """
        try:
            request = requests.get("%s/healthz" % self.api_uri)
            response_body = request.content
            request.close()
            _ = json.loads(response_body.decode())
        except Exception as e:
            display("%s %s" % (self.api_healthz.__name__, e))
            if first is True:
                time.sleep(0.5)
                self.api_healthz(False)
            else:
                raise

    def setUp(self):
        subprocess.call(["reset", "-q"])
        self.clean_sandbox()
        self.api_healthz()

    def clean_up_virtual_machine(self, name: str):
        for elt in [["virsh", "destroy", name], ["virsh", "undefine", name],
                    ["virsh", "vol-delete", "%s.qcow2" % name, "--pool", "default"]]:
            self.virsh(elt)

    def create_virtual_machine(self, name: str, nb_node: int, disk_gb=0):
        if disk_gb == 0:
            disk_opt = "size=10"
        else:
            disk_opt = "size=%d" % disk_gb
        virt_install = [
            "virt-install",
            "--name",
            "%s" % name,
            "--network=bridge:rack0,model=virtio",
            "--memory=%d" % self.get_optimized_memory(nb_node, disk_gb),
            "--vcpus=%d" % self.get_optimized_cpu(nb_node),
            "--cpu",
            "host",
            "--pxe",
            "--mac=%s" % self.generate_mac_from_name(name),
            "--disk",
            disk_opt,
            "--os-type=linux",
            "--os-variant=generic",
            "--noautoconsole",
            "--check=disk_size=off",
            "--boot=hd,network"
        ]
        return virt_install

    @staticmethod
    def generate_mac_from_name(name: str):
        """
        :param name: virtual machine name
        :return:
        """
        nb = int(re.match('.*-(\d)$', name).group(1)) + 1
        if nb > 99:
            raise AssertionError("machine number extracted from name is incoherent: %d %s" % (nb, name))
        return "54:52:00:00:00:%02d" % nb

    @staticmethod
    def virsh(cmd, assertion=False, v=None):
        ret = subprocess.call(cmd, stdout=v, stderr=v)
        if assertion is True and ret != 0:
            raise RuntimeError("\"%s\"" % " ".join(cmd))

    def fetch_discovery_interfaces(self):
        request = self.fetch_discovery()
        interfaces = [k["interfaces"] for k in request if request]
        return interfaces

    def fetch_discovery(self):
        request = requests.get("%s/discovery" % self.api_uri)
        response_body = request.content
        request.close()
        self.assertEqual(request.status_code, 200)
        disco_data = json.loads(response_body.decode())
        return disco_data

    def fetch_discovery_ignition_journal(self, uuid: str):
        request = requests.get("%s/discovery/ignition-journal/%s" % (self.api_uri, uuid))
        response_body = request.content
        request.close()
        self.assertEqual(request.status_code, 200)
        disco_data = json.loads(response_body.decode())
        return disco_data

    def kvm_restart_off_machines(self, to_start: list, tries=120):
        self.assertIs(list, type(to_start))
        self.assertGreater(len(to_start), 0)
        for j in range(tries):
            if len(to_start) == 0:
                break

            for i, m in enumerate(to_start):
                start = ["virsh", "start", "%s" % m]
                try:
                    self.virsh(start, assertion=True), display("")
                    to_start.pop(i)
                    time.sleep(self.testing_sleep_seconds)

                except RuntimeError:
                    # virsh raise this
                    pass

            time.sleep(self.testing_sleep_seconds)
        self.assertEqual(len(to_start), 0)

    def etcd_endpoint_health(self, ips: list, port: int, tries=30, verify=True, certs_name=""):
        self.assertIs(list, type(ips))
        self.assertGreater(len(ips), 0)
        certs = tuple()
        if certs_name:
            verify, certs = self._get_certificates(certs_name)
        for t in range(tries):
            if len(ips) == 0:
                break
            for i, ip in enumerate(ips):
                try:
                    endpoint = "https://%s:%d/health" % (ip, port)
                    request = requests.get(endpoint, verify=verify, cert=certs)
                    response_body = json.loads(request.content.decode())
                    request.close()
                    display("-> RESULT %s %s" % (endpoint, response_body))
                    sys.stdout.flush()
                    if response_body == {u"health": u"true"}:
                        ips.pop(i)
                        display("-> REMAIN %s for %s" % (str(ips), self.etcd_endpoint_health.__name__))
                        continue

                except Exception as e:
                    display(e)
                display("-> %d/%d NOT READY %s:%d for %s" % (t, tries, ip, port, self.etcd_endpoint_health.__name__))
                time.sleep(self.testing_sleep_seconds * 2)

        self.assertEqual(len(ips), 0)

    def _get_vault_uri_by_initier(self, ip: str, port: int, tries=30):
        vault_uri = ""
        for t in range(tries):
            try:
                endpoint = "https://%s:%d/v2/keys/initier" % (ip, port)
                request = requests.get(endpoint, verify=False)
                request.close()
                content = request.content
                vault_uri = json.loads(content.decode())["node"]["value"]
                display("-> RESULT %s: %s" % (endpoint, vault_uri))
                sys.stdout.flush()
                break
            except Exception as e:
                display(e)
            display(
                "-> %d/%d NOT READY initier %s:%d for %s" % (t, tries, ip, port, self.vault_self_certs.__name__))
            time.sleep(self.testing_sleep_seconds * 2)
        self.assertGreater(len(vault_uri), 0)
        return vault_uri

    def vault_self_certs(self, ip, port, tries=30):
        vault_uri = self._get_vault_uri_by_initier(ip, port, tries)
        token_vault_server = self._get_vault_token_in_etcd(ip, port, "token/vault/server", tries)
        self._vault_issue_certificate(
            "%s/v1/pki/vault/issue/server" % vault_uri, token_vault_server, verify=False, parent="vault",
            component="server")

    def _get_vault_token_in_etcd(self, ip: str, port: int, etcd_key: str, tries=30):
        token_vault_server = ""
        for t in range(tries):
            try:
                endpoint = "https://%s:%d/v2/keys/%s" % (ip, port, etcd_key)
                request = requests.get(endpoint, verify=False)
                content = request.content
                request.close()
                token_vault_server = json.loads(content.decode())["node"]["value"].replace("\n", "")
                break

            except Exception as e:
                display(e)
            display("-> %d/%d NOT READY token %s %s:%d for %s" % (
                t, tries, etcd_key, ip, port, self.vault_self_certs.__name__))
            time.sleep(self.testing_sleep_seconds * 2)
        self.assertGreater(len(token_vault_server), 0)
        return token_vault_server

    def _vault_issue_certificate(self, url: str, token: str, verify: bool, parent: str, component: str, tries=30):
        certs = ["certificate", "issuing_ca", "private_key"]
        content = dict()
        for t in range(tries):
            try:
                request = requests.post(
                    url,
                    headers={'X-Vault-Token': token},
                    verify=verify,
                    data=json.dumps({
                        "common_name": "enjoliver.local",
                        "ttl": "17520h",
                        "ip_sans": "%s" % self.api_ip,
                    }))
                request.close()
                content = json.loads(request.content.decode())["data"]
                break
            except Exception as e:
                display(e)
                time.sleep(self.testing_sleep_seconds * 2)

        for c in certs:
            filename_ext = "%s_%s.%s" % (parent, component, c)
            with open(os.path.join(self.test_certs_path, filename_ext), 'w') as f:
                f.write(content[c])
                display("vault issue %s token: %s -> %s" % (url, token, filename_ext))

    def vault_verifing_issuing_ca(self, ip: str, port: int):
        vault_uri = self._get_vault_uri_by_initier(ip, port, tries=2)
        r = requests.get("%s/v1/" % vault_uri,
                         verify=os.path.join(self.test_certs_path, "vault_server.issuing_ca"))
        r.close()
        self.assertEqual(404, r.status_code)
        self.assertEqual({"errors": []}, json.loads(r.content.decode()))

    def vault_issue_app_certs(self, ip: str, port: int, tries=30):
        vault_uri = self._get_vault_uri_by_initier(ip, port, tries=2)
        for vault_cert in [(parent, component) for parent, component in [
            ("etcd-kubernetes", "client"),
            ("etcd-fleet", "client"),
            ("kubernetes", "kube-apiserver"),
            ("kubernetes", "kubelet")
        ]]:
            for t in range(tries):
                parent, component = vault_cert[0], vault_cert[1]
                try:
                    token = self._get_vault_token_in_etcd(ip, port, "token/%s/%s" % (parent, component))
                    self._vault_issue_certificate(
                        "%s/v1/pki/%s/issue/%s" % (vault_uri, parent, component),
                        token,
                        verify=os.path.join(self.test_certs_path, "vault_server.issuing_ca"),
                        parent=parent,
                        component=component
                    )
                    break
                except Exception as e:
                    display(e)
                display("-> %d/%d NOT READY %s/%s %s for %s" % (
                    t, tries, parent, component, ip, self.vault_self_certs.__name__))
                time.sleep(self.testing_sleep_seconds)

    def _get_certificates(self, certs_name: str):
        verify, certs = True, tuple()
        if certs_name:
            verify = os.path.join(self.test_certs_path, "%s.issuing_ca" % certs_name)
            certs = (
                os.path.join(self.test_certs_path, "%s.certificate" % certs_name),
                os.path.join(self.test_certs_path, "%s.private_key" % certs_name)
            )
            for c in certs:
                self.assertTrue(os.path.exists(c))
            self.assertTrue(os.path.exists(verify))
        return verify, certs

    def save_unseal_key(self, ips: list):
        unseal_file = os.path.join(self.test_certs_path, "unseal.key")

        for ip in ips:
            stdout = subprocess.check_output([
                "ssh", "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "ConnectTimeout=1",
                "-i", self.ssh_private_key,
                "-lcore", ip, 'sudo grep "Unseal Key 1:" /etc/vault.d/keys | cut -f4 -d \' \''
            ]).decode().replace("\n", "")
            if stdout:
                with open(unseal_file, "w") as f:
                    f.write(stdout)
                break
        self.assertTrue(os.path.isfile(unseal_file))

    def unseal_all_vaults(self, ips: list, tries=30):
        with open(os.path.join(self.test_certs_path, "unseal.key")) as f:
            key = f.read()
        self.assertGreater(len(key), 0)
        for ip in ips:
            for t in range(tries):
                url = "https://%s:8200/v1/sys/unseal" % ip
                try:
                    request = requests.post(
                        url,
                        verify=os.path.join(self.test_certs_path, "vault_server.issuing_ca"),
                        data=json.dumps({
                            "key": key,
                        }))
                    content = json.loads(request.content.decode())
                    request.close()
                    self.assertFalse(content["sealed"])
                    request = requests.get(
                        "https://%s:8200/v1/" % ip,
                        verify=os.path.join(self.test_certs_path, "vault_server.issuing_ca"),
                    )
                    content = json.loads(request.content.decode())
                    request.close()
                    self.assertEqual([], content["errors"])
                    break
                except Exception as e:
                    display(e)
                display("-> NOT READY %d/%d %s %s key: %s" % (
                    t, tries, url, self.unseal_all_vaults.__name__, key))
                self.assertFalse(t == tries - 1)
                time.sleep(self.testing_sleep_seconds * 2)

    def etcd_member_len(self, ip: str, members_nb: int, port: int, tries=30, verify=True, certs_name=""):
        result = {}
        certs = tuple()
        if certs_name:
            verify, certs = self._get_certificates(certs_name)

        for t in range(tries):
            try:
                endpoint = "https://%s:%d/v2/members" % (ip, port)
                request = requests.get(endpoint, verify=verify, cert=certs)
                content = request.content
                request.close()
                result = json.loads(content.decode())
                display("-> RESULT %s %s" % (endpoint, result))
                sys.stdout.flush()
                if len(result["members"]) == members_nb:
                    break

            except Exception as e:
                display(e)
            display("-> %d/%d NOT READY %s:%d for %s" % (t, tries, ip, port, self.etcd_member_len.__name__))
            time.sleep(self.testing_sleep_seconds * 2)

        self.assertEqual(len(result["members"]), members_nb)

    def kubernetes_node_nb(self, api_server_ip: str, nodes_nb: int, tries=200):
        c = kubeclient.ApiClient(host="%s:%d" % (api_server_ip, self.ec.kubernetes_apiserver_insecure_port))
        core = kubeclient.CoreV1Api(c)
        items = []
        for t in range(tries):
            try:
                nodes = core.list_node()
                if nodes and len(nodes.items) == nodes_nb:
                    items = nodes.items
                    break

            except Exception as e:
                display(e)
            display("-> %d/%d NOT READY %s for %s %d/%d" % (
                t, tries, api_server_ip, self.kubernetes_node_nb.__name__, len(items), nodes_nb))
            time.sleep(self.testing_sleep_seconds)

        self.assertEqual(len(items), nodes_nb)

    def kube_apiserver_health(self, ips: list, tries=200):
        self.assertIs(list, type(ips))
        self.assertGreater(len(ips), 0)
        for t in range(tries):
            if len(ips) == 0:
                break
            for i, ip in enumerate(ips):
                try:
                    endpoint = "http://%s:%d/healthz" % (ip, self.ec.kubernetes_apiserver_insecure_port)
                    request = requests.get(endpoint)
                    response_body = request.content
                    request.close()
                    display("-> RESULT %s %s" % (endpoint, response_body))
                    if response_body == b"ok":
                        display("## kubectl -s %s:%d get cs" % (ip, self.ec.kubernetes_apiserver_insecure_port))
                        ips.pop(i)
                        display("-> REMAIN %s for %s" % (str(ips), self.kube_apiserver_health.__name__))
                        continue

                except Exception as e:
                    display(e)
                display("-> %d/%d NOT READY %s for %s" % (t + 1, tries, ip, self.kube_apiserver_health.__name__))
                time.sleep(self.testing_sleep_seconds)
        self.assertEqual(len(ips), 0)

    def create_tiller(self, api_server_ip: str):
        c = kubeclient.ApiClient(host="http://%s:%d" % (api_server_ip, self.ec.kubernetes_apiserver_insecure_port))

        with open("%s/manifests/tiller/tiller-service.yaml" % self.euid_path) as f:
            service_manifest = yaml.load(f)

        with open("%s/manifests/tiller/tiller-deploy.yaml" % self.euid_path) as f:
            deploy_manifest = yaml.load(f)

        with open("%s/manifests/tiller/tiller-service-account.yaml" % self.euid_path) as f:
            serviceaccount_manifest = yaml.load(f)

        with open("%s/manifests/tiller/clusterrolebinding.yaml" % self.euid_path) as f:
            clusterrolebinding_manifest = yaml.load(f)

        core, beta = kubeclient.CoreV1Api(c), kubeclient.ExtensionsV1beta1Api(c)
        rbac = kubeclient.RbacAuthorizationV1beta1Api(c)

        core.create_namespaced_service("kube-system", service_manifest)
        rbac.create_cluster_role_binding(clusterrolebinding_manifest)
        core.create_namespaced_service_account("kube-system", serviceaccount_manifest)
        beta.create_namespaced_deployment("kube-system", deploy_manifest)

    def pod_tiller_is_running(self, api_server_ip: str, tries=100):
        code = 0
        c = kubeclient.ApiClient(host="http://%s:%d" % (api_server_ip, self.ec.kubernetes_apiserver_insecure_port))
        core = kubeclient.CoreV1Api(c)
        for t in range(tries):
            if code == 200:
                break
            try:
                r = core.list_namespaced_pod("kube-system", label_selector="app=tiller")
                for p in r.items:
                    ip = p.status.pod_ip
                    try:
                        g = requests.get("http://%s:44135/liveness" % ip)
                        code = g.status_code
                        g.close()
                        display("-> RESULT %s %s for %s" % (ip, code, self.pod_tiller_is_running.__name__))
                    except Exception as e:
                        display("-> %d/%d NOT READY %s for %s %s" % (
                            t + 1, tries, ip, self.pod_tiller_is_running.__name__, e))
            except ValueError:
                display("-> %d/%d NOT READY %s for %s" % (
                    t + 1, tries, "ValueError", self.pod_tiller_is_running.__name__))

            time.sleep(self.testing_sleep_seconds)
        self.assertEqual(200, code)

    def _tiller_is_gc(self, node_ip):
        output = subprocess.check_output([
            "ssh", "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=1",
            "-i", self.ssh_private_key,
            "-lcore", node_ip,
            'sudo bash -c "/opt/bin/rkt l --no-legend | grep -c tiller"'
        ])
        tiller_containers = int(output.decode().replace("\n", ""))
        return tiller_containers == 1

    def tiller_can_restart(self, api_server_ip: str):
        c = kubeclient.ApiClient(
            host="http://%s:%d" % (api_server_ip, self.ec.kubernetes_apiserver_insecure_bind_address))
        core = kubeclient.CoreV1Api(c)
        r = core.list_namespaced_pod("kube-system", label_selector="app=tiller")
        pod_ip, node_ip, req, tiller_endpoint = "", "", "", ""
        for p in r.items:
            pod_ip = p.status.pod_ip
            node_ip = p.status.host_ip
            try:
                req = "http://%s:44135/liveness" % pod_ip
                g = requests.get(req)
                g.close()
                self.assertEqual(200, g.status_code)
                tiller_endpoint = "%s:44134" % pod_ip
                display("-> tiller endpoint to kill: %s" % tiller_endpoint)
                subprocess.check_output([
                    "ssh", "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    "-o", "ConnectTimeout=1",
                    "-i", self.ssh_private_key,
                    "-lcore", node_ip,
                    'sudo /usr/bin/pkill tiller'
                ])
                break
            except Exception as e:
                display(e)
        with self.assertRaises(requests.ConnectionError):
            g = requests.get(req)
            g.close()

        ts = time.time()
        for i in range(10):
            try:
                new_tiller_endpoint = self._get_tiller_grpc_endpoint(api_server_ip=api_server_ip)
                display("-> new tiller endpoint: %s" % new_tiller_endpoint)
                break
            except Exception as e:
                display(e)
                time.sleep(1)

        new_tiller_endpoint = self._get_tiller_grpc_endpoint(api_server_ip=api_server_ip)
        self.assertNotEqual(self._get_tiller_grpc_endpoint(api_server_ip=api_server_ip), tiller_endpoint)
        display("-> polling tiller Pod %s during 70s or until its GC" % new_tiller_endpoint)
        while time.time() < ts + 120:
            try:
                loop_tiller_endpoint = self._get_tiller_grpc_endpoint(api_server_ip=api_server_ip)
            except RuntimeWarning:
                time.sleep(1)
                loop_tiller_endpoint = self._get_tiller_grpc_endpoint(api_server_ip=api_server_ip)
            self.assertEqual(new_tiller_endpoint, loop_tiller_endpoint)
            if self._tiller_is_gc(node_ip):
                return
            time.sleep(1)
        raise AssertionError("tiller is not gc on node %s" % node_ip)

    def _get_tiller_grpc_endpoint(self, api_server_ip: str):
        c = kubeclient.ApiClient(host="http://%s:%d" % (api_server_ip, self.ec.kubernetes_apiserver_insecure_port))
        core = kubeclient.CoreV1Api(c)
        r = core.list_namespaced_pod("kube-system", label_selector="app=tiller")
        exception = None
        for p in r.items:
            ip = p.status.pod_ip
            try:
                g = requests.get("http://%s:44135/liveness" % ip)
                g.close()
                self.assertEqual(200, g.status_code)
                return "%s:44134" % ip
            except Exception as e:
                display(e)
                exception = e
        raise exception

    def create_helm_etcd_backup(self, api_server_ip: str, etcd_app_name: str):
        tiller = self._get_tiller_grpc_endpoint(api_server_ip)
        c = kubeclient.ApiClient(host="http://%s:%d" % (api_server_ip, self.ec.kubernetes_apiserver_insecure_port))
        core = kubeclient.CoreV1Api(c)
        try:
            core.create_namespace(body={"kind": "Namespace", "apiVersion": "v1", "metadata": {"name": "backup"}})
        except Exception as e:
            self.assertEqual("Conflict", e.reason)

        ret = subprocess.call([
            self.helm_bin,
            "--host",
            tiller,
            "install",
            "-f",
            "%s/manifests/etcd3-backup/%s.yaml" % (self.euid_path, etcd_app_name),
            "%s/manifests/etcd3-backup/" % self.euid_path
        ])
        self.assertEqual(0, ret)

    def create_helm_by_name(self, api_server_ip: str, name: str):
        tiller = self._get_tiller_grpc_endpoint(api_server_ip)
        ret = subprocess.call([
            self.helm_bin,
            "--host",
            tiller,
            "install",
            "%s/manifests/%s" % (self.euid_path, name)
        ])
        self.assertEqual(0, ret)

    def _snapshot_status(self, core: kubeclient.CoreV1Api, etcd_app_name: str, tries: int):
        for t in range(tries):
            r = core.list_namespaced_pod("backup", label_selector="etcd=%s" % etcd_app_name)
            for p in r.items:
                ip = p.status.host_ip
                if p.status.phase != "Succeeded":
                    display("%d/%d pod %s status.phase: %s" % (t, tries, p.metadata.name, p.status.phase))
                    continue
                try:
                    stdout = subprocess.check_output([
                        "ssh", "-o", "StrictHostKeyChecking=no",
                        "-o", "UserKnownHostsFile=/dev/null",
                        "-o", "ConnectTimeout=1",
                        "-i", self.ssh_private_key,
                        "-lcore", ip,
                        'sudo /opt/bin/etcdctl3 snapshot status /var/lib/backup/etcd3/%s.snap -w json' % etcd_app_name
                    ])
                    return json.loads(stdout.decode())
                except Exception as e:
                    display(e)

            time.sleep(self.testing_sleep_seconds)

    def etcd_backup_done(self, api_server_ip: str, etcd_app_name: str, tries=120):
        c = kubeclient.ApiClient(host="%s:%d" % (api_server_ip, self.ec.kubernetes_apiserver_insecure_port))
        core = kubeclient.CoreV1Api(c)
        summary = self._snapshot_status(core, etcd_app_name, tries)
        for k in ["revision", "totalKey", "totalSize"]:
            self.assertGreater(summary[k], 0)

    def daemonset_node_exporter_are_running(self, ips: list, tries=200):
        assert type(ips) is list
        assert len(ips) > 0
        for t in range(tries):
            if len(ips) == 0:
                break
            for i, ip in enumerate(ips):
                try:
                    g = requests.get("http://%s:9100" % ip)
                    code = g.status_code
                    g.close()
                    display("-> RESULT %s %s" % (ip, code))
                    if code == 200:
                        ips.pop(i)
                        display("-> REMAIN %s for %s" % (str(ips), self.daemonset_node_exporter_are_running.__name__))
                        continue

                except Exception as e:
                    display(e)
                display("-> %d/%d NOT READY %s for %s" % (
                    t + 1, tries, ip, self.daemonset_node_exporter_are_running.__name__))
                time.sleep(self.testing_sleep_seconds)

        self.assertEqual(len(ips), 0)

    def get_optimized_memory(self, nb_nodes: int, disk: int):
        mem_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        mem_gib = mem_bytes / (1024. ** 3)
        node_memory = (mem_gib // nb_nodes) * 1024
        default_memory = self.ram_kvm_node_memory_mb * 0.8 if disk else self.ram_kvm_node_memory_mb
        return default_memory * 1.2 if node_memory > default_memory else default_memory

    @staticmethod
    def get_optimized_cpu(nb_nodes: int):
        cpu = float(multiprocessing.cpu_count())
        cores = cpu / nb_nodes
        return int(round(cores))

    def kubectl_proxy(self, proxy_port: int):
        def run():
            cmd = [
                "%s/hyperkube/hyperkube" % self.project_path,
                "kubectl",
                "--kubeconfig",
                os.path.join(self.tests_path, "testing_kubeconfig.yaml"),
                "proxy",
                "-p",
                "%d" % proxy_port
            ]
            display("-> %s" % " ".join(cmd))
            os.execve(cmd[0], cmd, os.environ)

        return run

    def create_kubeconfig(self, api_server_ip: str):
        with open("%s/manifests/kubeconfig/clusterrolebinding.yaml" % self.euid_path) as f:
            clusterrolebinding_manifest = yaml.load(f)

        c = kubeclient.ApiClient(host="http://%s:%d" % (api_server_ip, self.ec.kubernetes_apiserver_insecure_port))
        rbac = kubeclient.RbacAuthorizationV1beta1Api(c)
        rbac.create_cluster_role_binding(clusterrolebinding_manifest)

        kube_config = {
            'preferences': {'colors': True},
            'users': [
                {
                    'user': {
                        'client-key': '%s/kubernetes_kubelet.private_key' % self.test_certs_path,
                        'client-certificate': '%s/kubernetes_kubelet.certificate' % self.test_certs_path
                    },
                    'name': 'enjoliver.local'
                }
            ],
            'kind': 'Config',
            'apiVersion': 'v1',
            'clusters': [
                {
                    'cluster': {
                        'server': "https://%s:6443" % api_server_ip,
                        'certificate-authority': '%s/kubernetes_kubelet.issuing_ca' % self.test_certs_path
                    },
                    'name': 'enjoliver'
                }
            ],
            'contexts': [
                {
                    'name': 'e',
                    'context': {
                        'cluster': 'enjoliver',
                        'namespace': 'kube-system',
                        'user': 'enjoliver.local'
                    }
                }
            ],
            'current-context': 'e'
        }
        with open(os.path.join(self.tests_path, "testing_kubeconfig.yaml"), "w") as kc:
            yaml.dump(kube_config, kc)

    def iteractive_usage(self, stop="/tmp/e.stop", api_server_ip=None, fns=None):
        display("-> Starting %s" % self.iteractive_usage.__name__)
        kp, proxy_port = None, 8001
        if api_server_ip:
            self.create_kubeconfig(api_server_ip)
            kp = multiprocessing.Process(target=self.kubectl_proxy(proxy_port=proxy_port))
            kp.start()
            maxi = 12
            for i in range(maxi):
                if kp.is_alive():
                    try:
                        r = requests.get("http://127.0.0.1:%d/healthz" % proxy_port)
                        r.close()
                        if r.status_code == 200:
                            display(
                                "\n#####################################\n"
                                "mkdir -pv ~/.kube\n"
                                "cat << EOF >> ~/.kube/config\n"
                                "apiVersion: v1\n"
                                "clusters:\n"
                                "- cluster:\n"
                                "    server: http://127.0.0.1:8001\n"
                                "  name: enjoliver\n"
                                "contexts:\n"
                                "- context:\n"
                                "    cluster: enjoliver\n"
                                "    namespace: default\n"
                                "    user: ""\n"
                                "  name: e\n"
                                "current-context: e\n"
                                "kind: Config\n"
                                "preferences:\n"
                                "  colors: true\n"
                                "EOF\n"
                                "kubectl config use-context e\n"
                                "#####################################\n"
                            )
                            break
                    except Exception as e:
                        display("-> %d/%d %s" % (i + 1, maxi, e))
                time.sleep(0.5)

        with open(stop, "w") as f:
            f.write("")
        os.chmod(stop, 777)

        try:
            while os.path.isfile(stop) is True and os.stat(stop).st_size == 0:
                if fns:
                    [fn() for fn in fns]
                if int(time.time()) % 120 == 0:
                    display("-> Stop with \"sudo rm -v\" %s or \"echo 1 > %s\"" % (stop, stop))
                time.sleep(self.wait_setup_teardown)
            if api_server_ip and kp.is_alive():
                kp.terminate()
                kp.join(timeout=5)
        finally:
            display("-> Stopping %s" % self.iteractive_usage.__name__)

    def replace_ignition_metadata(self, metadata, new_value):
        req = requests.get("%s/scheduler" % self.api_uri)
        scheduler = json.loads(req.content.decode())
        req.close()
        for mac in scheduler:
            req = requests.post("%s/lifecycle/rolling/mac=%s" % (self.api_uri, mac))
            req.close()

        for j in os.listdir("%s/groups/" % self.test_matchbox_path):
            if j == "discovery.json" or ".json" not in j:
                continue
            with open("%s/groups/%s" % (self.test_matchbox_path, j), 'r') as f:
                group = json.loads(f.read())
            group["metadata"][metadata] = new_value
            with open("%s/groups/%s" % (self.test_matchbox_path, j), 'w') as f:
                json.dump(group, f, indent=4)
