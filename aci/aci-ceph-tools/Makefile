CWD=$(shell pwd)

PROJECT=$(CWD)/../..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci
DEBIAN=debian

ACI_NAME=ceph-tools

default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

install: $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(ACI_NAME)
	IMAGE=$(ACI)/aci-$(ACI_NAME) make -C $(RUNTIME) install

test: install
	@echo ENV IMAGE=$(ACI)/aci-$(ACI_NAME)
	IMAGE=$(ACI)/aci-$(ACI_NAME) make -C $(RUNTIME) test

push: $(DEBIAN) test
	@echo ENV IMAGE=$(ACI)/aci-$(ACI_NAME)
	IMAGE=$(ACI)/aci-$(ACI_NAME) make -C $(RUNTIME) push

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean: gc
	IMAGE=$(ACI)/aci-$(ACI_NAME) make -C $(RUNTIME) clean

re: clean default

re_quick:
	@echo ENV IMAGE=$(ACI)/aci-$(ACI_NAME)
	IMAGE=$(ACI)/aci-$(ACI_NAME) make -C $(RUNTIME) push
