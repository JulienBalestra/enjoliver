CWD=$(shell pwd)

BOOTCFG_DIR=bootcfg_dir
BOOTCFG=$(BOOTCFG_DIR)/bootcfg
BOOTCFG_RELEASE=https://github.com/coreos/coreos-baremetal/releases/download/v0.4.0/coreos-baremetal-v0.4.0-linux-amd64.tar.gz

RKT_DIR=rkt_dir
RKT_DIR_DATA=$(RKT_DIR)/data
RKT=$(RKT_DIR)/rkt
RKT_RELEASE=https://github.com/coreos/rkt/releases/download/v1.17.0/rkt-v1.17.0.tar.gz


CHAIN_IP_PORT=172.15.0.1:5000
KKK=undionly.kkkpxe
ISO=ipxe.iso

EUID= $(shell id -u -r)
ifneq ($(EUID), 0)
	ROOT=1
endif

PROJECT=$(CWD)/../..
ENV_NAME=env
PYTHON=$(PROJECT)/$(ENV_NAME)/bin/python

default: $(BOOTCFG) $(RKT) $(PYTHON) $(KKK) $(ISO)

bootcfg_assets:
	@echo Run as USER
	test $(ROOT)
	make -C $(PROJECT) assets

$(PYTHON):
	@echo Run as USER
	test $(ROOT)
	ls $(PROJECT)/$(ENV_NAME) || virtualenv $(PROJECT)/$(ENV_NAME)
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
	$(CWD)/$(RKT) --dir=$(CWD)/$(RKT_DIR)/data fetch \
    		--insecure-options=all $(RKT_DIR)/stage1-coreos.aci
	$(CWD)/$(RKT) --dir=$(CWD)/$(RKT_DIR)/data image list

fetch: $(RKT)
	$(CWD)/$(RKT) --dir=$(CWD)/$(RKT_DIR)/data fetch \
		--insecure-options=all quay.io/coreos/dnsmasq:v0.3.0
	$(CWD)/$(RKT) --dir=$(CWD)/$(RKT_DIR)/data image list

dnsmasq:
	@file $(RKT)
	@cat $(CWD)/dnsmasq-metal0.conf
	$(CWD)/$(RKT) \
		--interactive \
		--dir=$(CWD)/$(RKT_DIR)/data \
		--mount volume=config,target=/etc/dnsmasq.conf \
		--local-config=$(CWD) \
		run --insecure-options=all \
		quay.io/coreos/dnsmasq:v0.3.0 \
		--net=host \
		--volume config,kind=host,source=$(CWD)/dnsmasq-metal0.conf

gc:
	test ! -e $(CWD)/$(RKT) || $(CWD)/$(RKT) --dir=$(CWD)/$(RKT_DIR)/data gc --grace-period=0s

gci:
	test ! -e $(CWD)/$(RKT) || $(CWD)/$(RKT) --dir=$(CWD)/$(RKT_DIR)/data image gc --grace-period=0s

clean:
	rm -Rfv $(BOOTCFG_DIR)
	rm -Rfv $(RKT_DIR)
	rm -v $(ISO)
	rm -v $(KKK)
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

check_euid_basic: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) -m unittest discover euid/basic/

check_euid_basic_iso: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/basic/test_kvm_basic_iso.py

check_euid_basic_pxe: $(PYTHON)
	PYTHONPATH=$(shell pwd)/../.. $(PYTHON) euid/basic/test_kvm_basic_pxe.py

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
