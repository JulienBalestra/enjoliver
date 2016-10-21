CWD=$(shell pwd)

BOOTCFG_DIR=bootcfg_dir
BOOTCFG=$(BOOTCFG_DIR)/bootcfg
BOOTCFG_RELEASE=https://github.com/coreos/coreos-baremetal/releases/download/v0.4.0/coreos-baremetal-v0.4.0-linux-amd64.tar.gz

RKT_DIR=rkt_dir
RKT_DIR_NET=$(RKT_DIR)/etc/net.d
RKT_DIR_DATA=$(RKT_DIR)/data
RKT=$(RKT_DIR)/rkt
RKT_RELEASE=https://github.com/coreos/rkt/releases/download/v1.17.0/rkt-v1.17.0.tar.gz

default: $(BOOTCFG) $(RKT)

$(BOOTCFG):
	mkdir -pv $(BOOTCFG_DIR)
	curl -Lf $(BOOTCFG_RELEASE) -o $(BOOTCFG).tar.gz
	tar -C $(BOOTCFG_DIR) -xzf $(BOOTCFG).tar.gz --strip-components=1
	file $(BOOTCFG)

$(RKT):
	mkdir -pv $(RKT_DIR)
	mkdir -pv $(RKT_DIR_DATA)
	mkdir -pv $(RKT_DIR_NET)
	curl -Lf $(RKT_RELEASE) -o $(RKT).tar.gz
	tar -C $(RKT_DIR) -xzf $(RKT).tar.gz --strip-components=1
	ln -sv $(CWD)/10-metal.conf $(RKT_DIR_NET)/10-metal.conf
	$(CWD)/$(RKT) --dir=$(CWD)/$(RKT_DIR)/data fetch \
    		--insecure-options=all $(RKT_DIR)/stage1-coreos.aci
	file $(RKT)

fetch:
	$(CWD)/$(RKT) --dir=$(CWD)/$(RKT_DIR)/data fetch \
        --insecure-options=all quay.io/coreos/dnsmasq:v0.3.0

dnsmasq:
	@file $(RKT)
	$(CWD)/$(RKT) \
		--interactive \
		--dir=$(CWD)/$(RKT_DIR)/data \
		--mount volume=config,target=/etc/dnsmasq.conf \
		--local-config=$(RKT_DIR)/etc \
		run --insecure-options=all \
		quay.io/coreos/dnsmasq:v0.3.0 \
        --net=metal0 \
        --volume config,kind=host,source=$(CWD)/dnsmasq-metal0.conf

gc:
	$(CWD)/$(RKT) --dir=$(CWD)/$(RKT_DIR)/data gc --grace-period=0s
	$(CWD)/$(RKT) --dir=$(CWD)/$(RKT_DIR)/data image gc --grace-period=0s

fclean: gc
	rm -Rfv $(BOOTCFG_DIR)
	rm -Rfv $(RKT_DIR)

check: $(TARGET)
	PYTHONPATH=$(shell pwd)/../.. python -m unittest discover unit/
	PYTHONPATH=$(shell pwd)/../.. python -m unittest discover inte/
	PYTHONPATH=$(shell pwd)/../.. python -m unittest discover func/

check_fast: $(TARGET)
	PYTHONPATH=$(shell pwd)/../.. python -m unittest discover unit/
	PYTHONPATH=$(shell pwd)/../.. python -m unittest discover inte/

re: fclean default
