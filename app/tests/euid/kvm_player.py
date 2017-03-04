import datetime
import json
import multiprocessing
import os
import shutil
import socket
import subprocess
import sys
import time
import unittest

import requests
import yaml
from kubernetes import client as kc

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
                print(r.read())
        os.remove(f)
    except OSError:
        pass
    return d


@unittest.skipIf(os.geteuid() != 0, "TestKVMDiscovery need privilege")
@unittest.skipIf(is_virtinstall() != 0, "TestKVMDiscovery need virt-install")
class KernelVirtualMachinePlayer(unittest.TestCase):
    """
    This class is used by all Kernel Virtual Machine testing suite
    Override the setUpClass by selecting your custom environment with the following catalog:
    >>> @classmethod
    >>> def setUpClass(cls):
    >>>     cls.check_requirements()
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
    matchbox_bin = "%s/matchbox/matchbox" % runtime_path
    acserver_bin = "%s/acserver/acserver" % runtime_path

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
    ec = configs.EnjoliverConfig(importer=__file__)

    @staticmethod
    def pause(t=600):
        """
        Sleep for eventual side testing or tests/s.sh ...
        :param t: 10 minutes
        :return: None
        """
        try:
            print("==> sleep %d..." % t)
            time.sleep(t)
        except KeyboardInterrupt:
            pass
        finally:
            print("==> sleep finish")

    @staticmethod
    def process_target_matchbox():
        os.environ["MATCHBOX_PATH"] = KernelVirtualMachinePlayer.test_matchbox_path
        cmd = [
            "%s/manage.py" % KernelVirtualMachinePlayer.project_path,
            "matchbox",
        ]
        print("PID  -> %s\n"
              "exec -> %s" % (os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.environ["TERM"] = "xterm"
        os.execve(cmd[0], cmd, os.environ)

    @staticmethod
    def process_target_acserver():
        cmd = [
            "%s" % KernelVirtualMachinePlayer.acserver_bin,
            "%s/ac-config.yml" % KernelVirtualMachinePlayer.runtime_path
        ]
        print("PID  -> %s\n"
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
                os.environ["ENJOLIVER_BACKUP_BUCKET_NAME"] = "bbcenjoliver-dev"
        except (IOError, ValueError):
            pass

        cmd = [
            "%s/manage.py" % KernelVirtualMachinePlayer.project_path,
            "gunicorn",
        ]
        print("PID  -> %s\n"
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
            "quay.io/coreos/dnsmasq:v0.3.0",
            "--insecure-options=all",
            "--net=host",
            "--interactive",
            "--set-env=TERM=%s" % os.getenv("TERM", "xterm"),
            "--uuid-file-save=/tmp/dnsmasq.uuid",
            "--volume",
            "resolv,kind=host,source=/etc/resolv.conf",
            "--volume",
            "config,kind=host,source=%s/dnsmasq-rack0.conf" % KernelVirtualMachinePlayer.tests_path
        ]
        print("PID  -> %s\n"
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
        print("PID  -> %s\n"
              "exec -> %s" % (os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execve(cmd[0], cmd, os.environ)
        os._exit(2)  # Should not happen

    @staticmethod
    def dns_masq_running():
        print("DNSMASQ probing...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = 1
        for i in range(120):
            result = sock.connect_ex(('172.20.0.1', 53))
            if result == 0:
                break
            time.sleep(0.5)
            if i % 10 == 0:
                print("DNSMASQ still NOT ready")
        sock.close()
        assert result == 0
        print("DNSMASQ ready")
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
                print(" GET -> %s : %s" % (url, e))
            time.sleep(0.5)
        r = requests.get(url)
        r.close()

    @classmethod
    def check_requirements(cls):
        # TODO validate the assets in this method
        if os.geteuid() != 0:
            raise RuntimeError("Need to be root EUID==%d" % os.geteuid())

        cls.clean_sandbox()

        if os.path.isfile(KernelVirtualMachinePlayer.rkt_bin) is False or \
                        os.path.isfile(KernelVirtualMachinePlayer.matchbox_bin) is False or \
                        os.path.isfile(KernelVirtualMachinePlayer.acserver_bin) is False:
            print("Call 'make runtime' as user for:\n"
                  "- %s\n" % KernelVirtualMachinePlayer.rkt_bin +
                  "- %s\n" % KernelVirtualMachinePlayer.matchbox_bin +
                  "- %s\n" % KernelVirtualMachinePlayer.acserver_bin)
            exit(2)
        print("PID -> %s" % os.getpid())

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
            "quay.io/coreos/dnsmasq:v0.3.0",
            "--insecure-options=all",
            "--net=rack0",
            "--interactive",
            "--set-env=TERM=%s" % os.getenv("TERM", "xterm"),
            "--exec",
            "/bin/true"]
        print("call %s" % " ".join(cmd))
        ret = subprocess.call(cmd)
        print("Bridge w/ iptables creation exitcode:%d" % ret)
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
        time.sleep(0.5)
        assert cls.p_acserver.is_alive() is True
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
                print("TERM -> %s %s" % (p.pid, p.name))
                p.terminate()
                p.join(10)
                if p.is_alive():
                    os.kill(p.pid, 9)
                print("END -> %s %s" % (p.exitcode, p.name))
            print("EXITED -> %s %s" % (p.exitcode, p.name))

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
                    print("-> remove %s" % f)
                    os.remove("%s/%s" % (d, f))

    def api_healthz(self, first=True):
        try:
            request = requests.get("%s/healthz" % self.api_uri)
            response_body = request.content
            request.close()
            health = json.loads(response_body.decode())
            self.assertTrue(health["global"])
        except Exception as e:
            print("%s %s" % (self.api_healthz.__name__, e))
            if first is True:
                time.sleep(0.5)
                self.api_healthz(False)
            else:
                raise

    def setUp(self):
        subprocess.call(["reset", "-q"])
        self.clean_sandbox()
        self.api_healthz()

    def virsh(self, cmd, assertion=False, v=None):
        ret = subprocess.call(cmd, stdout=v, stderr=v)
        if assertion is True and ret != 0:
            raise RuntimeError("\"%s\"" % " ".join(cmd))

    def fetch_discovery_interfaces(self):
        request = requests.get("%s/discovery/interfaces" % self.api_uri)
        response_body = request.content
        request.close()
        self.assertEqual(request.status_code, 200)
        interfaces = json.loads(response_body.decode())
        return interfaces

    def fetch_discovery(self):
        request = requests.get("%s/discovery" % self.api_uri)
        response_body = request.content
        request.close()
        self.assertEqual(request.status_code, 200)
        disco_data = json.loads(response_body.decode())
        return disco_data

    def fetch_discovery_ignition_journal(self, uuid):
        request = requests.get("%s/discovery/ignition-journal/%s" % (self.api_uri, uuid))
        response_body = request.content
        request.close()
        self.assertEqual(request.status_code, 200)
        disco_data = json.loads(response_body.decode())
        return disco_data

    def kvm_restart_off_machines(self, to_start, tries=120):
        assert type(to_start) is list
        assert len(to_start) > 0
        for j in range(tries):
            if len(to_start) == 0:
                break

            for i, m in enumerate(to_start):
                start = ["virsh", "start", "%s" % m]
                try:
                    self.virsh(start, assertion=True), print("")
                    to_start.pop(i)
                    time.sleep(self.testing_sleep_seconds)

                except RuntimeError:
                    # virsh raise this
                    pass

            time.sleep(self.testing_sleep_seconds)
        self.assertEqual(len(to_start), 0)

    def etcd_endpoint_health(self, ips, port, tries=30):
        assert type(ips) is list
        assert len(ips) > 0
        for t in range(tries):
            if len(ips) == 0:
                break
            for i, ip in enumerate(ips):
                try:
                    endpoint = "http://%s:%d/health" % (ip, port)
                    request = requests.get(endpoint)
                    response_body = json.loads(request.content.decode())
                    request.close()
                    print("-> RESULT %s %s" % (endpoint, response_body))
                    sys.stdout.flush()
                    if response_body == {u"health": u"true"}:
                        ips.pop(i)
                        print("-> REMAIN %s for %s" % (str(ips), self.etcd_endpoint_health.__name__))

                except requests.exceptions.ConnectionError:
                    print("-> %d/%d NOT READY %s for %s" % (t, tries, ip, self.etcd_endpoint_health.__name__))
                    time.sleep(self.testing_sleep_seconds * 2)

        self.assertEqual(len(ips), 0)

    def etcd_member_len(self, ip, members_nb, port, tries=30):
        result = {}
        for t in range(tries):
            try:
                endpoint = "http://%s:%d/v2/members" % (ip, port)
                request = requests.get(endpoint)
                content = request.content
                request.close()
                result = json.loads(content.decode())
                print("-> RESULT %s %s" % (endpoint, result))
                sys.stdout.flush()
                if len(result["members"]) == members_nb:
                    break

            except requests.exceptions.ConnectionError:
                print("-> %d/%d NOT READY %s for %s" % (t, tries, ip, self.etcd_member_len.__name__))
                time.sleep(self.testing_sleep_seconds * 2)

        self.assertEqual(len(result["members"]), members_nb)

    def etcd_member_k8s_minions(self, ip, nodes_nb, tries=200):
        result = {}
        for t in range(tries):
            try:
                endpoint = "http://%s:2379/v2/keys/registry/minions" % ip
                request = requests.get(endpoint)
                content = request.content
                request.close()
                result = json.loads(content.decode())
                sys.stdout.flush()
                if result and len(result["node"]["nodes"]) == nodes_nb:
                    break

            except (requests.exceptions.ConnectionError, KeyError):
                pass
            print("-> NOT READY %s %s" % (ip, self.etcd_member_k8s_minions.__name__))
            time.sleep(self.testing_sleep_seconds)

        self.assertEqual(len(result["node"]["nodes"]), nodes_nb)

    def k8s_api_health(self, ips, tries=200):
        assert type(ips) is list
        assert len(ips) > 0
        for t in range(tries):
            if len(ips) == 0:
                break
            for i, ip in enumerate(ips):
                try:
                    endpoint = "http://%s:8080/healthz" % ip
                    request = requests.get(endpoint)
                    response_body = request.content
                    request.close()
                    print("-> RESULT %s %s" % (endpoint, response_body))
                    sys.stdout.flush()
                    if response_body == b"ok":
                        print("## kubectl -s %s:8080 get cs" % ip)
                        ips.pop(i)
                        print("-> REMAIN %s for %s" % (str(ips), self.k8s_api_health.__name__))

                except requests.exceptions.ConnectionError:
                    print("-> %d/%d NOT READY %s for %s" % (t + 1, tries, ip, self.k8s_api_health.__name__))
                    time.sleep(self.testing_sleep_seconds)
        self.assertEqual(len(ips), 0)

    def create_nginx_deploy(self, api_server_ip):
        with open("%s/manifests/nginx-deploy.yaml" % self.euid_path) as f:
            nginx = yaml.load(f)

        c = kc.ApiClient(host="%s:8080" % api_server_ip)
        b = kc.ExtensionsV1beta1Api(c)
        b.create_namespaced_deployment("default", nginx)

    def create_nginx_daemon_set(self, api_server_ip):
        with open("%s/manifests/nginx-daemonset.yaml" % self.euid_path) as f:
            nginx = yaml.load(f)

        c = kc.ApiClient(host="%s:8080" % api_server_ip)
        b = kc.ExtensionsV1beta1Api(c)
        b.create_namespaced_daemon_set("default", nginx)

    def pod_nginx_is_running(self, api_server_ip, tries=100):
        code = 0
        c = kc.ApiClient(host="%s:8080" % api_server_ip)
        core = kc.CoreV1Api(c)
        for t in range(tries):
            if code == 404:
                break
            try:
                r = core.list_namespaced_pod("default")
                for p in r.items:
                    ip = p.status.pod_ip
                    try:
                        g = requests.get("http://%s" % ip)
                        code = g.status_code
                        g.close()
                        print("-> RESULT %s %s" % (ip, code))
                        sys.stdout.flush()
                    except requests.exceptions.ConnectionError:
                        print("-> %d/%d NOT READY %s for %s" % (
                            t + 1, tries, ip, self.pod_nginx_is_running.__name__))
            except ValueError:
                print("-> %d/%d NOT READY %s for %s" % (
                    t + 1, tries, "ValueError", self.pod_nginx_is_running.__name__))

            time.sleep(self.testing_sleep_seconds)
        self.assertEqual(404, code)

    def daemon_set_nginx_are_running(self, ips, tries=200):
        assert type(ips) is list
        assert len(ips) > 0
        for t in range(tries):
            if len(ips) == 0:
                break
            for i, ip in enumerate(ips):
                try:
                    g = requests.get("http://%s" % ip)
                    code = g.status_code
                    g.close()
                    print("-> RESULT %s %s" % (ip, code))
                    sys.stdout.flush()
                    if code == 404:
                        ips.pop(i)
                        print("-> REMAIN %s for %s" % (str(ips), self.daemon_set_nginx_are_running.__name__))

                except requests.exceptions.ConnectionError:
                    print("-> %d/%d NOT READY %s for %s" % (
                        t + 1, tries, ip, self.daemon_set_nginx_are_running.__name__))
                    time.sleep(self.testing_sleep_seconds)

        self.assertEqual(len(ips), 0)

    @staticmethod
    def get_optimized_memory(nb_nodes):
        mem_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        mem_gib = mem_bytes / (1024. ** 3)
        usable_mem_gib = mem_gib * (1.5 if mem_gib > 10 else 1.2)
        return (usable_mem_gib // nb_nodes) * 1024

    @staticmethod
    def get_optimized_cpu(nb_nodes):
        cpu = float(multiprocessing.cpu_count())
        cores = cpu / nb_nodes
        return int(round(cores))

    def kubectl_proxy(self, api_server_uri, proxy_port):
        def run():
            cmd = [
                "%s/hyperkube/hyperkube" % self.project_path,
                "kubectl",
                "-s",
                "%s" % api_server_uri,
                "proxy",
                "-p",
                "%d" % proxy_port
            ]
            print("-> %s" % " ".join(cmd))
            os.execve(cmd[0], cmd, os.environ)

        return run

    def iteractive_usage(self, stop="/tmp/e.stop", api_server_uri=None, fns=None):
        print("-> Starting %s" % self.iteractive_usage.__name__)
        kp, proxy_port = None, 8001
        if api_server_uri:
            kp = multiprocessing.Process(target=self.kubectl_proxy(api_server_uri, proxy_port=proxy_port))
            kp.start()
            maxi = 12
            for i in range(maxi):
                if kp.is_alive():
                    try:
                        r = requests.get("http://127.0.0.1:%d/healthz" % proxy_port)
                        r.close()
                        if r.status_code == 200:
                            print("## kubectl -s 127.0.0.1:%d get cs" % proxy_port)
                            break
                    except Exception as e:
                        print("-> %d/%d %s" % (i + 1, maxi, type(e)))
                time.sleep(0.5)

        with open(stop, "w") as f:
            f.write("")
        os.chmod(stop, 777)

        try:
            while os.path.isfile(stop) is True and os.stat(stop).st_size == 0:
                if fns:
                    [fn() for fn in fns]
                if int(time.time()) % 30 == 0:
                    print("-> Stop with \"sudo rm -v\" %s or \"echo 1 > %s\"" % (stop, stop))
                time.sleep(self.wait_setup_teardown)
            if api_server_uri and kp.is_alive():
                kp.terminate()
                kp.join(timeout=5)
        finally:
            print("-> Stopping %s" % self.iteractive_usage.__name__)
