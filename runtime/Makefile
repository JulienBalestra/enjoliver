CWD=$(shell pwd)


# DGR
DGR_VERSION=v78
DGR_GITHUB_DOWNLOAD=https://github.com/blablacar/dgr/releases/download
DGR_TAR=dgr-$(DGR_VERSION)-linux-amd64.tar.gz
DGR_GITHUB=$(DGR_GITHUB_DOWNLOAD)/$(DGR_VERSION)/$(DGR_TAR)
DGR_DIR=$(CWD)/dgr
DGR=$(DGR_DIR)/dgr
DGR_DOWNLOAD_TAR=$(DGR_DIR)/$(DGR_TAR)


# RKT
RKT_VERSION=v1.21.0
RKT_GITHUB_DOWNLOAD=https://github.com/coreos/rkt/releases/download
RKT_TAR=rkt-$(RKT_VERSION).tar.gz
RKT_GITHUB=$(RKT_GITHUB_DOWNLOAD)/$(RKT_VERSION)/$(RKT_TAR)
RKT_DIR=$(CWD)/rkt
RKT=$(RKT_DIR)/rkt
RKT_DOWNLOAD_TAR=$(RKT_DIR)/$(RKT_TAR)


# BOOTCFG
BOOTCFG_VERSION=v0.4.2
BOOTCFG_GITHUB_DOWNLOAD=https://github.com/coreos/coreos-baremetal/releases/download
BOOTCFG_TAR=coreos-baremetal-$(BOOTCFG_VERSION)-linux-amd64.tar.gz
BOOTCFG_GITHUB=$(BOOTCFG_GITHUB_DOWNLOAD)/$(BOOTCFG_VERSION)/$(BOOTCFG_TAR)
BOOTCFG_DIR=$(CWD)/bootcfg
BOOTCFG=$(BOOTCFG_DIR)/bootcfg
BOOTCFG_DOWNLOAD_TAR=$(BOOTCFG_DIR)/$(BOOTCFG_TAR)


default: setup

$(BOOTCFG_DOWNLOAD_TAR):
	mkdir -pv $(BOOTCFG_DIR)
	curl -fL $(BOOTCFG_GITHUB) -o $(BOOTCFG_DOWNLOAD_TAR)

$(BOOTCFG): $(BOOTCFG_DOWNLOAD_TAR)
	tar -C $(BOOTCFG_DIR) -xzf $(BOOTCFG_DIR)/$(BOOTCFG_TAR) --strip-components=1
	$(BOOTCFG) --version


$(DGR_DOWNLOAD_TAR):
	mkdir -pv $(DGR_DIR)
	curl -fL $(DGR_GITHUB) -o $(DGR_DOWNLOAD_TAR)

$(DGR): $(DGR_DOWNLOAD_TAR)
	tar -C $(DGR_DIR) -xzf $(DGR_DIR)/$(DGR_TAR) --strip-components=1


$(RKT_DOWNLOAD_TAR):
	mkdir -pv $(RKT_DIR)
	curl -fL $(RKT_GITHUB) -o $(RKT_DOWNLOAD_TAR)

$(RKT): $(RKT_DOWNLOAD_TAR)
	tar -C $(RKT_DIR) -xzf $(RKT_DOWNLOAD_TAR) --strip-components=1
	$(CWD)/config.py
	$(RKT) --local-config=$(CWD) fetch \
    		--insecure-options=all $(RKT_DIR)/stage1-coreos.aci
	$(RKT) --local-config=$(CWD) image list


setup: $(RKT) $(DGR)

gc:
	$(RKT) --local-config=$(CWD) gc --grace-period=0s

gci:
	$(RKT) --local-config=$(CWD) image gc --grace-period=0s

build: $(DGR) $(RKT)
	@echo ENV eg: IMAGE=$(CWD)/../aci/aci-base
	test $(IMAGE)
	$(DGR) -H $(CWD) config
	$(DGR) -H $(CWD) build -W $(IMAGE)
	$(RKT) --local-config=$(CWD) image list
	$(RKT) --local-config=$(CWD) gc --grace-period=0s

install: $(DGR) $(RKT)
	@echo ENV eg: IMAGE=$(CWD)/../aci/aci-base
	test $(IMAGE)
	$(DGR) -H $(CWD) install -W $(IMAGE)
	$(RKT) --local-config=$(CWD) image list

clean: $(DGR)
	@echo ENV eg: IMAGE=$(CWD)/../aci/aci-base
	test $(IMAGE)
	$(DGR) -H $(CWD) clean -W $(IMAGE)
	$(RKT) --local-config=$(CWD) image gc --grace-period=0s
	$(RKT) --local-config=$(CWD) image list

fclean:
	rm -Rf $(DGR_DIR) || true
	rm -Rf $(RKT_DIR) || true
	rm -Rf data || true
	rm -Rf renders/*.render || true
	rm -Rf target || true

.PHONY: $(DGR) $(RKT) setup build install clean fclean
