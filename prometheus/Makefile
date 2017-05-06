CWD=$(shell pwd)

PROJECT=$(CWD)/..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci


DEBIAN=debian
PROMETHEUS=prometheus
NODE_EXPORTER=node-exporter


default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

prepare: $(DEBIAN)

install: prepare
	@echo ENV IMAGE=$(ACI)/aci-$(PROMETHEUS)
	IMAGE=$(ACI)/aci-$(PROMETHEUS) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(NODE_EXPORTER) make -C $(RUNTIME) install

test: install
	@echo ENV IMAGE=$(ACI)/aci-$(PROMETHEUS)
	IMAGE=$(ACI)/aci-$(PROMETHEUS) make -C $(RUNTIME) test
	IMAGE=$(ACI)/aci-$(NODE_EXPORTER) make -C $(RUNTIME) test

push: test
	@echo ENV IMAGE=$(ACI)/aci-$(PROMETHEUS)
	IMAGE=$(ACI)/aci-$(PROMETHEUS) make -C $(RUNTIME) push
	IMAGE=$(ACI)/aci-$(NODE_EXPORTER) make -C $(RUNTIME) push

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean: gc
	IMAGE=$(ACI)/aci-$(PROMETHEUS) make -C $(RUNTIME) gc

fclean: clean
	IMAGE=$(ACI)/aci-$(GO) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(BUILDER_HYPERKUBE) make -C $(RUNTIME) clean

re: clean default

re_quick:
	@echo ENV IMAGE=$(ACI)/aci-$(PROMETHEUS)
	IMAGE=$(ACI)/aci-$(PROMETHEUS) make -C $(RUNTIME) build
	IMAGE=$(ACI)/aci-$(PROMETHEUS) make -C $(RUNTIME) push