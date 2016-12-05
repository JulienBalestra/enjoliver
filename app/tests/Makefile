CWD=$(shell pwd)

BOOTCFG_DIR=bootcfg_dir
BOOTCFG=$(BOOTCFG_DIR)/bootcfg
BOOTCFG_RELEASE=https://github.com/coreos/coreos-baremetal/releases/download/v0.4.0/coreos-baremetal-v0.4.0-linux-amd64.tar.gz

RKT_DIR=rkt_dir
RKT_DIR_DATA=$(RKT_DIR)/data
RKT=$(RKT_DIR)/rkt
RKT_RELEASE=https://github.com/coreos/rkt/releases/download/v1.19.0/rkt-v1.19.0.tar.gz


CHAIN_IP_PORT=172.20.0.1:5000
KKK=undionly.kkkpxe
ISO=ipxe.iso

EUID= $(shell id -u -r)
ifneq ($(EUID), 0)
	ROOT=1
endif

PROJECT=$(CWD)/../..
ENV_NAME=env
PYTHON=$(PROJECT)/$(ENV_NAME)/bin/python

TESTING_RSA=testing.id_rsa

default: $(BOOTCFG) $(RKT) $(PYTHON) $(TESTING_RSA)

bootcfg_assets:
	@echo Run as USER
	test $(ROOT)
	make -C $(PROJECT) assets

$(PYTHON):
	@echo Run as USER
	test $(ROOT)
	ls $(PROJECT)/$(ENV_NAME) || \
		virtualenv2 --python=python2.7 $(PROJECT)/$(ENV_NAME) || \
		virtualenv --python=python2.7 $(PROJECT)/$(ENV_NAME)
	$(PROJECT)/$(ENV_NAME)/bin/pip install -r $(PROJECT)/requirements.txt
	$(PYTHON) --version


$(BOOTCFG):
	@echo Run as USER
	test $(ROOT)
	mkdir -pv $(BOOTCFG_DIR)
	curl -Lf $(BOOTCFG_RELEASE) -o $(BOOTCFG).tar.gz
	tar -C $(BOOTCFG_DIR) -xzf $(BOOTCFG).tar.gz --strip-components=1
	file $(BOOTCFG)

$(RKT):
	@echo Run as USER
	test $(ROOT)
	mkdir -pv $(RKT_DIR)
	mkdir -pv $(RKT_DIR_DATA)
	curl -Lf $(RKT_RELEASE) -o $(RKT).tar.gz
	tar -C $(RKT_DIR) -xzf $(RKT).tar.gz --strip-components=1
	$(CWD)/gen_config.py
	$(CWD)/$(RKT) --local-config=$(CWD) fetch \
    		--insecure-options=all $(RKT_DIR)/stage1-coreos.aci
	$(CWD)/$(RKT) --local-config=$(CWD) image list

fetch: $(RKT)
	$(CWD)/$(RKT) --local-config=$(CWD) fetch \
		--insecure-options=all quay.io/coreos/dnsmasq:v0.3.0
	$(CWD)/$(RKT) --local-config=$(CWD) image list

dnsmasq:
	@file $(RKT)
	@cat $(CWD)/dnsmasq-rack0.conf
	$(CWD)/$(RKT) \
		--interactive \
		--mount volume=config,target=/etc/dnsmasq.conf \
		--local-config=$(CWD) \
		run --insecure-options=all \
		quay.io/coreos/dnsmasq:v0.3.0 \
		--net=host \
		--volume config,kind=host,source=$(CWD)/dnsmasq-rack0.conf

gc:
	test ! -e $(CWD)/$(RKT) || $(CWD)/$(RKT) --local-config=$(CWD) gc --grace-period=0s

gci:
	test ! -e $(CWD)/$(RKT) || $(CWD)/$(RKT) --local-config=$(CWD) image gc --grace-period=0s

$(TESTING_RSA):
	ssh-keygen -f $(CWD)/$(TESTING_RSA) -t rsa -N ''
	mkdir -vp $(CWD)/test_bootcfg/ssh_authorized_keys/
	ln -sv $(CWD)/$(TESTING_RSA).pub $(CWD)/test_bootcfg/ssh_authorized_keys/

clean:
	rm -Rfv $(BOOTCFG_DIR)
	rm -Rfv $(RKT_DIR)
	rm -v $(ISO)
	rm -v $(KKK)
	rm -v $(TESTING_RSA)*
	rm -Rfv test_bootcfg/ssh_authorized_keys
	rm -v paths.d/*.json
	make -C $(PROJECT)/chain clean

fclean: clean gci gc

check_fast: default $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover unit/
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover inte/

check: default $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover ./

check_assets: default $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover assets/

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

check_euid_basic: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover euid/basic/

check_euid_basic_iso: $(PYTHON) $(ISO)
	KVM_ISO=run PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/basic/test_kvm_basic_iso.py

check_euid_basic_pxe: $(PYTHON) 
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/basic/test_kvm_basic_pxe.py

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
