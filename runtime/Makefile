CWD=$(shell pwd)

# DGR
DGR_VERSION=v86
DGR_GITHUB_DOWNLOAD=https://github.com/blablacar/dgr/releases/download
DGR_TAR=dgr-$(DGR_VERSION)-linux-amd64.tar.gz
DGR_GITHUB=$(DGR_GITHUB_DOWNLOAD)/$(DGR_VERSION)/$(DGR_TAR)
DGR_DIR=$(CWD)/dgr
DGR=$(DGR_DIR)/dgr
DGR_DOWNLOAD_TAR=$(DGR_DIR)/$(DGR_TAR)

# RKT
RKT_VERSION=v1.27.0
RKT_GITHUB_DOWNLOAD=https://github.com/coreos/rkt/releases/download
RKT_TAR=rkt-$(RKT_VERSION).tar.gz
RKT_GITHUB=$(RKT_GITHUB_DOWNLOAD)/$(RKT_VERSION)/$(RKT_TAR)
RKT_DIR=$(CWD)/rkt
RKT=$(RKT_DIR)/rkt
RKT_DOWNLOAD_TAR=$(RKT_DIR)/$(RKT_TAR)
RKT_DATASTORE=/tmp/rkt-data

# MATCHBOX
MATCHBOX_VERSION=v0.5.0
MATCHBOX_GITHUB_DOWNLOAD=https://github.com/coreos/matchbox/releases/download
MATCHBOX_TAR=matchbox-$(MATCHBOX_VERSION)-linux-amd64.tar.gz
MATCHBOX_GITHUB=$(MATCHBOX_GITHUB_DOWNLOAD)/$(MATCHBOX_VERSION)/$(MATCHBOX_TAR)
MATCHBOX_DIR=$(CWD)/matchbox
MATCHBOX=$(MATCHBOX_DIR)/matchbox
MATCHBOX_DOWNLOAD_TAR=$(MATCHBOX_DIR)/$(MATCHBOX_TAR)

# HELM
HELM_VERSION=v2.5.0
HELM_GOOGLE_STORAGE_DOWNLOAD=https://storage.googleapis.com/kubernetes-helm
HELM_TAR=helm-$(HELM_VERSION)-linux-amd64.tar.gz
HELM_GOOGLE_STORAGE=$(HELM_GOOGLE_STORAGE_DOWNLOAD)/$(HELM_TAR)
HELM_DIR=$(CWD)/helm
HELM=$(HELM_DIR)/helm
HELM_DOWNLOAD_TAR=$(HELM_DIR)/$(HELM_TAR)

# ACSERVER
ACSERVER_DIR=$(CWD)/acserver
ACSERVER=$(ACSERVER_DIR)/acserver

default: dev_setup

prod_setup: $(MATCHBOX)

$(ACSERVER):
	mkdir -pv $(ACSERVER_DIR)
	curl -fL https://github.com/JulienBalestra/acserver/releases/download/v0.1.0/acserver.tar.gz | tar -C $(ACSERVER_DIR) -xzvf -
	$(ACSERVER) -V

$(HELM_DOWNLOAD_TAR):
	mkdir -pv $(HELM_DIR)
	curl -fL $(HELM_GOOGLE_STORAGE) -o $(HELM_DOWNLOAD_TAR)

$(HELM): $(HELM_DOWNLOAD_TAR)
	@test -x $(HELM) || tar -C $(HELM_DIR) -xzf $(HELM_DOWNLOAD_TAR) --strip-components=1

$(MATCHBOX_DOWNLOAD_TAR):
	mkdir -pv $(MATCHBOX_DIR)
	curl -fL $(MATCHBOX_GITHUB) -o $(MATCHBOX_DOWNLOAD_TAR)

$(MATCHBOX): $(MATCHBOX_DOWNLOAD_TAR)
	@$(MATCHBOX) --version || tar -C $(MATCHBOX_DIR) -xzf $(MATCHBOX_DIR)/$(MATCHBOX_TAR) --strip-components=1
	$(MATCHBOX) --version

$(DGR_DOWNLOAD_TAR):
	mkdir -pv $(DGR_DIR)
	curl -fL $(DGR_GITHUB) -o $(DGR_DOWNLOAD_TAR)

$(DGR): $(DGR_DOWNLOAD_TAR)
	@test -x $(DGR) || tar -C $(DGR_DIR) -xzf $(DGR_DIR)/$(DGR_TAR) --strip-components=1

$(RKT_DOWNLOAD_TAR):
	mkdir -pv $(RKT_DIR)
	curl -fL $(RKT_GITHUB) -o $(RKT_DOWNLOAD_TAR)

$(RKT): $(RKT_DOWNLOAD_TAR)
	@test -x $(RKT) || tar -C $(RKT_DIR) -xzf $(RKT_DOWNLOAD_TAR) --strip-components=1
	@$(CWD)/config.py
	@mkdir -p $(RKT_DATASTORE)
	@ln -sf $(RKT_DATASTORE) $(CWD)/data || true

dev_setup: $(MATCHBOX) $(RKT) $(DGR) $(ACSERVER) $(HELM)

create_rack0:
	@file $(RKT)
	$(RKT) \
		--local-config=$(CWD) \
		--net=rack0 \
		run --insecure-options=all \
		coreos.com/rkt/stage1-coreos \
		--exec /bin/bash -- -c exit 0
gc:
	@$(RKT) --local-config=$(CWD) gc --grace-period=0s

gci:
	@$(RKT) --local-config=$(CWD) image gc --grace-period=0s

build: $(DGR) $(RKT)
	@test $(IMAGE)
	@$(DGR) -H $(CWD) config
	@$(DGR) -H $(CWD) build -W $(IMAGE) -k -c
	@$(RKT) --local-config=$(CWD) gc --grace-period=0s

install: $(DGR) $(RKT)
	@test $(IMAGE)
	@$(DGR) -H $(CWD) install -W $(IMAGE)

push: $(DGR) $(RKT)
	@test $(IMAGE)
	@$(DGR) -H $(CWD) push -W $(IMAGE)

test: $(DGR) $(RKT)
	@test $(IMAGE)
	@$(DGR) -H $(CWD) test -W $(IMAGE)

clean: $(DGR)
	@test $(IMAGE)
	@$(DGR) -H $(CWD) clean -W $(IMAGE)
	@$(RKT) --local-config=$(CWD) gc --grace-period=0s
	@$(RKT) --local-config=$(CWD) image gc --grace-period=0s

fclean:
	rm -Rf $(DGR_DIR) || true
	rm -Rf $(RKT_DIR) || true
	rm -Rf $(MATCHBOX_DIR) || true
	rm -Rf $(ACSERVER_DIR)/* || true
	rm -Rf data || true
	rm -Rf renders/*.render || true
	rm -Rf target || true

.PHONY: $(DGR) $(RKT) $(ACSERVER) $(HELM) setup build install clean fclean
