VERSION=v78
CWD=$(shell pwd)

GITHUB_REPO=https://github.com/blablacar/dgr/releases/download
TAR=dgr-$(VERSION)-linux-amd64.tar.gz
GITHUB_DGR=$(GITHUB_REPO)/$(VERSION)/$(TAR)

BIN=bin
DGR=$(BIN)/dgr
DGR_TARGET=target

RKT_DIR=rkt_dir
RKT_DIR_DATA=$(RKT_DIR)/data
RKT=$(RKT_DIR)/rkt
RKT_RELEASE=https://github.com/coreos/rkt/releases/download/v1.19.0/rkt-v1.19.0.tar.gz

DGR_CONFIG=config.yml


default: $(DGR) $(RKT)


$(RKT):
	mkdir -pv $(RKT_DIR)
	mkdir -pv $(RKT_DIR_DATA)
	curl -Lf $(RKT_RELEASE) -o $(RKT).tar.gz
	tar -C $(RKT_DIR) -xzf $(RKT).tar.gz --strip-components=1
	$(CWD)/$(RKT) --local-config=$(CWD) fetch \
    		--insecure-options=all $(RKT_DIR)/stage1-coreos.aci
	$(CWD)/$(RKT) --local-config=$(CWD) image list

$(DGR):
	make -C ../ submodules
	curl -LO $(GITHUB_DGR)
	mkdir -pv $(BIN)
	mkdir -pv $(DGR_TARGET)
	tar -C $(BIN) -xzf $(TAR) --strip-components=1
	$(CWD)/gen_config.py

fclean:
	$(CWD)/$(RKT) --local-config=$(CWD) image gc --grace-period=0s
	$(CWD)/$(RKT) --local-config=$(CWD) gc --grace-period=0s
	rm -Rfv $(BIN) $(TAR) $(DGR_TARGET) || true
	rm -Rfv $(RKT_DIR) $(RKT_DIR_DATA) || true
	rm -v config.yml || true
	rm -v paths.d/paths.json || true

build: $(DGR) $(RKT)
	@echo ENV eg: IMAGE=$(CWD)/dgr/examples/aci-base/
	test $(IMAGE)
	$(CWD)/$(DGR) -H $(CWD) config
	$(CWD)/$(DGR) -H $(CWD) build -W $(IMAGE)
	$(CWD)/$(RKT) --local-config=$(CWD) image list

install: $(DGR) $(RKT)
	@echo ENV eg: IMAGE=dgr/examples/aci-base/
	test $(IMAGE)
	$(CWD)/$(DGR) -H $(CWD) install -W $(IMAGE)
	$(CWD)/$(RKT) --local-config=$(CWD) image list

clean: $(DGR)
	@echo ENV eg: IMAGE=dgr/examples/aci-base/
	test $(IMAGE)
	$(CWD)/$(DGR) -H $(CWD) clean -W $(IMAGE)
