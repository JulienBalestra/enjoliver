CWD=$(shell pwd)


CHAIN_IP_PORT=172.20.0.1:5000
KKK=undionly.kkkpxe
ISO=ipxe.iso

EUID= $(shell id -u -r)
ifneq ($(EUID), 0)
	ROOT=1
endif

PROJECT=$(CWD)/../..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt

ENV_NAME=env
PYTHON=$(PROJECT)/$(ENV_NAME)/bin/python3

TESTING_RSA=testing.id_rsa


check:
	PATH=$(PROJECT)/env/bin:$(PATH) PYTHONPATH=$(PROJECT) $(PYTHON) -m unittest discover ./


runtime: $(TESTING_RSA)
	$(CWD)/config.py


create_rack0:
	@file $(RKT)
	$(RKT) \
		--local-config=$(CWD) \
		--net=rack0 \
		run --insecure-options=all \
		coreos.com/rkt/stage1-coreos \
		--exec /bin/bash -- -c exit 0

gc:
	$(RKT) --local-config=$(CWD) gc --grace-period=0s

gci:
	$(RKT) --local-config=$(CWD) image gc --grace-period=0s

$(TESTING_RSA):
	ssh-keygen -f $(CWD)/$(TESTING_RSA) -t rsa -N ''
	mkdir -vp $(CWD)/test_matchbox/ssh_authorized_keys/
	ln -svf $(CWD)/$(TESTING_RSA).pub $(CWD)/test_matchbox/ssh_authorized_keys/

clean:
	rm -v $(ISO) || true
	rm -v $(KKK) || true
	rm -v $(TESTING_RSA)* || true
	rm -Rfv test_matchbox/ssh_authorized_keys || true
	rm -v paths.d/*.json || true
	rm -Rfv euid/ignition_journal || true
	rm -Rfv euid/euid.sqlite || true
	rm -Rfv inte/ignition_journal || true
	rm -Rfv inte/dbs || true
	rm -Rfv unit/ignition_journal || true
	rm -Rfv unit/dbs || true

fclean: clean gci gc

check_euid_fail_fast: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover euid/ -f

check_euid: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover euid/

check_euid_discovery: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover euid/discovery/

check_euid_discovery_client: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/discovery/test_kvm_discovery_client.py

check_euid_k8s_basic: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/k8s/test_kvm_k8s_basic.py

check_euid_k8s_fast: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/k8s/test_kvm_k8s_fast.py

check_euid_it_k8s_fast: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. TEST=TestKVMK8SFast0 $(PYTHON) euid/k8s/test_kvm_k8s_fast.py

check_euid_k8s_etcd_operator: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/k8s/test_kvm_k8s_etcd_operator.py

check_euid_it_k8s_etcd_operator: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. TEST=TestKVMK8SEtcdOperator0 $(PYTHON) euid/k8s/test_kvm_k8s_etcd_operator.py

check_euid_basic: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover euid/basic/

check_euid_basic_iso: $(PYTHON) $(ISO) runtime
	KVM_ISO=run PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/basic/test_kvm_basic_iso.py

check_euid_basic_pxe: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/basic/test_kvm_basic_pxe.py

check_euid_plans_enjolivage: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/plans/test_kvm_plan_k8s_enjolivage.py

check_euid_it_plans_enjolivage: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. TEST=TestKVMK8sEnjolivage0 $(PYTHON) euid/plans/test_kvm_plan_k8s_enjolivage.py

check_euid_it_plans_enjolivage_disk_4_nodes: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. DISK_OK=yes TEST=TestKVMK8sEnjolivageDisk0 $(PYTHON) euid/plans/test_kvm_plan_k8s_enjolivage_disk.py

check_euid_it_plans_enjolivage_disk_2_nodes: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. DISK_OK=yes TEST=TestKVMK8sEnjolivageDisk1 $(PYTHON) euid/plans/test_kvm_plan_k8s_enjolivage_disk.py

check_euid_plans_enjolivage_disk: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. DISK_OK=yes $(PYTHON) euid/plans/test_kvm_plan_k8s_enjolivage_disk.py

check_euid_plans_enjolivage_disk_lifecycle: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. DISK_OK=yes $(PYTHON) euid/plans/test_kvm_plan_k8s_enjolivage_disk_lifecycle.py

check_euid_kvm_player: $(PYTHON) runtime
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/test_kvm_player.py

$(KKK):
	@echo Run as USER
	test $(ROOT)
	CHAIN_IP_PORT=$(CHAIN_IP_PORT) make -C $(PROJECT)/chain $(KKK)
	cp -v $(PROJECT)/chain/ipxe/src/bin/$(KKK) $(CWD)/$(KKK)
	file $(KKK)

$(ISO):
	@echo Run as USER
	test $(ROOT)
	CHAIN_IP_PORT=$(CHAIN_IP_PORT) make -C $(PROJECT)/chain $(ISO)
	cp -v $(PROJECT)/chain/ipxe/src/bin/$(ISO) $(CWD)/$(ISO)
	file $(ISO)

re: clean default
