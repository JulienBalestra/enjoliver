CWD=$(shell pwd)

PROJECT=$(CWD)/../..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

UBUNTU=ubuntu
RKT_ACI=rkt

default: push

$(UBUNTU):
	@echo ENV IMAGE=$(ACI)/aci-$(UBUNTU)
	IMAGE=$(ACI)/aci-$(UBUNTU) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(UBUNTU) make -C $(RUNTIME) push

test: $(UBUNTU)
	@echo ENV IMAGE=$(ACI)/aci-$(RKT_ACI)
	IMAGE=$(ACI)/aci-$(RKT_ACI) make -C $(RUNTIME) test

push: test
	@echo ENV IMAGE=$(ACI)/aci-$(RKT_ACI)
	IMAGE=$(ACI)/aci-$(RKT_ACI) make -C $(RUNTIME) push

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean: gc
	IMAGE=$(ACI)/aci-$(RKT_ACI) make -C $(RUNTIME) clean

fclean: clean

re: clean default
