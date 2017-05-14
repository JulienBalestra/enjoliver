CWD=$(shell pwd)

PROJECT=$(CWD)/../..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci


DEBIAN=debian
CNI=cni


default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

test: $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(CNI)
	IMAGE=$(ACI)/aci-$(CNI) make -C $(RUNTIME) test

push: test
	@echo ENV IMAGE=$(ACI)/aci-$(CNI)
	IMAGE=$(ACI)/aci-$(CNI) make -C $(RUNTIME) push

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean: gc
	IMAGE=$(ACI)/aci-$(CNI) make -C $(RUNTIME) clean

fclean: clean

re: clean default
