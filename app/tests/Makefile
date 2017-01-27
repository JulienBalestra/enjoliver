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
PYTHON=$(PROJECT)/$(ENV_NAME)/bin/python

TESTING_RSA=testing.id_rsa

default: validate $(PYTHON) $(TESTING_RSA)

validate:
	make -C $(PROJECT) validate

$(PYTHON):
	@echo Run as USER
	test $(ROOT)
	ls $(PROJECT)/$(ENV_NAME) || \
		virtualenv2 --python=python2.7 $(PROJECT)/$(ENV_NAME) || \
		virtualenv --python=python2.7 $(PROJECT)/$(ENV_NAME)
	$(PROJECT)/$(ENV_NAME)/bin/pip install -r $(PROJECT)/requirements.txt
	$(PYTHON) --version

runtime:
	make -C $(RUNTIME)
	$(CWD)/config.py


dnsmasq:
	@file $(RKT)
	@cat $(CWD)/dnsmasq-rack0.conf
	$(RKT) \
		--interactive \
		--mount volume=config,target=/etc/dnsmasq.conf \
		--mount volume=resolv,target=/etc/resolv.conf \
		--local-config=$(CWD) \
		run --insecure-options=all \
		quay.io/coreos/dnsmasq:v0.3.0 \
		--net=host \
		--volume config,kind=host,source=$(CWD)/dnsmasq-rack0.conf \
		--volume resolv,kind=host,source=/etc/resolv.conf

create_rack0:
	@file $(RKT)
	@cat $(CWD)/dnsmasq-rack0.conf
	$(RKT) \
		--interactive \
		--local-config=$(CWD) \
		--net=rack0 \
		run --insecure-options=all \
		quay.io/coreos/dnsmasq:v0.3.0 \
		--exec /bin/true

gc:
	$(RKT) --local-config=$(CWD) gc --grace-period=0s

gci:
	$(RKT) --local-config=$(CWD) image gc --grace-period=0s

ngrok_api:
	$(RKT) run --local-config=$(CWD) --interactive --net=rack0 \
	quay.io/julienbalestra/ngrok \
	--exec ngrok -- http 172.20.0.1:5000

ngrok_k8s:
	echo $(K8S_IP_PORT)
	test $(K8S_IP_PORT)
	$(RKT) run --local-config=$(CWD) --interactive --net=rack0 \
	quay.io/julienbalestra/ngrok \
	--exec ngrok -- http $(K8S_IP_PORT)

$(TESTING_RSA):
	ssh-keygen -f $(CWD)/$(TESTING_RSA) -t rsa -N ''
	mkdir -vp $(CWD)/test_bootcfg/ssh_authorized_keys/
	cp -v $(CWD)/$(TESTING_RSA).pub $(CWD)/test_bootcfg/ssh_authorized_keys/

clean:
	rm -v $(ISO) || true
	rm -v $(KKK) || true
	rm -v $(TESTING_RSA)* || true
	rm -Rfv test_bootcfg/ssh_authorized_keys || true
	rm -v paths.d/*.json || true
	rm -Rfv euid/ignition_journal || true
	rm -Rfv euid/euid.sqlite || true
	rm -Rfv inte/ignition_journal || true
	rm -Rfv inte/dbs || true
	rm -Rfv unit/ignition_journal || true
	rm -Rfv unit/dbs || true

fclean: clean gci gc

check_fast: default $(PYTHON)
	SKIP_ASSETS=TRUE PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover ./

check: default $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover ./

check_assets: default $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover assets/

check_euid_fail_fast: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover euid/ -f

check_euid: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover euid/

check_euid_discovery: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover euid/discovery/

check_euid_discovery_scheduler: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/discovery/test_kvm_discovery_scheduler.py

check_euid_discovery_client: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/discovery/test_kvm_discovery_client.py

check_euid_k8s_basic: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/k8s/test_kvm_k8s_basic.py

check_euid_k8s_fast: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/k8s/test_kvm_k8s_fast.py

check_euid_it_k8s_fast: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. TEST=TestKVMK8SFast0 $(PYTHON) euid/k8s/test_kvm_k8s_fast.py

check_euid_basic: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover euid/basic/

check_euid_basic_iso: $(PYTHON) $(ISO)
	KVM_ISO=run PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/basic/test_kvm_basic_iso.py

check_euid_basic_pxe: $(PYTHON) 
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/basic/test_kvm_basic_pxe.py

check_euid_plans_all_in_one: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/plans/test_kvm_plan_all_in_one.py

check_euid_plans_enjolivage: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/plans/test_kvm_plan_k8s_enjolivage.py

check_euid_it_plans_enjolivage: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. TEST=TestKVMK8sEnjolivage0 $(PYTHON) euid/plans/test_kvm_plan_k8s_enjolivage.py

check_euid_kvm_player: $(PYTHON)
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
