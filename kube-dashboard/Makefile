CWD=$(shell pwd)

PROJECT=$(CWD)/..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci


DEBIAN=debian
GO=go
NODEJS=nodejs
BUILDER_HYPERKUBE=builder-hyperkube
DASHBOARD=kube-dashboard


default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

$(GO): $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(GO)
	IMAGE=$(ACI)/aci-$(GO) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(GO) make -C $(RUNTIME) push

$(NODEJS): $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(GO)
	IMAGE=$(ACI)/aci-$(NODEJS) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(NODEJS) make -C $(RUNTIME) push

$(BUILDER_HYPERKUBE): $(GO)
	@echo ENV IMAGE=$(ACI)/aci-$(BUILDER_HYPERKUBE)
	IMAGE=$(ACI)/aci-$(BUILDER_HYPERKUBE) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

prepare: $(GO) $(BUILDER_HYPERKUBE) $(NODEJS)

install: prepare
	@echo ENV IMAGE=$(ACI)/aci-$(DASHBOARD)
	IMAGE=$(ACI)/aci-$(DASHBOARD) make -C $(RUNTIME) install

test: install
	@echo ENV IMAGE=$(ACI)/aci-$(DASHBOARD)
	IMAGE=$(ACI)/aci-$(HYPERKUBE) make -C $(RUNTIME) push

push: test
	@echo ENV IMAGE=$(ACI)/aci-$(DASHBOARD)
	IMAGE=$(ACI)/aci-$(DASHBOARD) make -C $(RUNTIME) push

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean: gc
	IMAGE=$(ACI)/aci-$(DASHBOARD) make -C $(RUNTIME) clean

fclean: clean
	IMAGE=$(ACI)/aci-$(GO) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(BUILDER_HYPERKUBE) make -C $(RUNTIME) clean

re: clean default

re_quick:
	@echo ENV IMAGE=$(ACI)/aci-$(DASHBOARD)
	IMAGE=$(ACI)/aci-$(DASHBOARD) make -C $(RUNTIME) build
	IMAGE=$(ACI)/aci-$(DASHBOARD) make -C $(RUNTIME) push