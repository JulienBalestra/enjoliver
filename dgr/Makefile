VERSION=77
CWD=$(shell pwd)

GITHUB_REPO=https://github.com/blablacar/dgr/releases/download
TAR=dgr-linux-amd64-$(VERSION).tar.gz
GITHUB_DGR=$(GITHUB_REPO)/$(VERSION)/$(TAR)

BIN=bin
DGR=$(BIN)/dgr
DGR_TARGET=target

RKT_DIR=rkt_dir
RKT_DIR_DATA=$(RKT_DIR)/data
RKT=$(RKT_DIR)/rkt
RKT_RELEASE=https://github.com/coreos/rkt/releases/download/v1.17.0/rkt-v1.17.0.tar.gz

DGR_CONFIG=config.yml

EUID= $(shell id -u -r)
ifneq ($(EUID), 0)
	ROOT=1
endif


default: $(DGR) $(RKT) conf

conf:
	$(CWD)/gen_config.py

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

$(DGR):
	@echo Run as USER
	test $(ROOT)
	make -C ../ submodules
	curl -LO $(GITHUB_DGR)
	mkdir -pv $(BIN)
	mkdir -pv $(DGR_TARGET)
	tar -C $(BIN) -xzf $(TAR)

clean:
	rm -Rfv $(BIN) $(TAR) $(DGR_TARGET) || true
	rm -Rfv $(RKT_DIR) $(RKT_DIR_DATA) || true
	rm -v config.yml || true
	rm -v path.d/paths.json || true

build:
	@echo ENV eg: IMAGE=dgr/examples/aci-base/
	test $(IMAGE)
	$(CWD)/$(DGR) -H $(CWD) -L debug build -W $(IMAGE)

install:
	@echo ENV eg: IMAGE=dgr/examples/aci-base/
	test $(IMAGE)
	$(CWD)/$(DGR) -H $(CWD) install -W $(IMAGE)
	$(CWD)/$(RKT) --dir=$(CWD)/$(RKT_DIR)/data image list