CWD=$(shell pwd)

PROJECT=$(CWD)/../..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

ACI_NAME=rookd

default: push

install:
	@echo ENV IMAGE=$(ACI)/aci-$(ACI_NAME)
	IMAGE=$(ACI)/aci-$(ACI_NAME) make -C $(RUNTIME) install

test: install
	@echo ENV IMAGE=$(ACI)/aci-$(ACI_NAME)
	IMAGE=$(ACI)/aci-$(ACI_NAME) make -C $(RUNTIME) test

push: test
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