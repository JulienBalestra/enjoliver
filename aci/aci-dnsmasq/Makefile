CWD=$(shell pwd)

PROJECT=$(CWD)/../..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

DEBIAN=debian

ACI_IMAGE=dnsmasq


default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

install: $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-lldp
	IMAGE=$(ACI)/aci-$(ACI_IMAGE) make -C $(RUNTIME) install

push: $(DEBIAN)
	IMAGE=$(ACI)/aci-$(ACI_IMAGE) make -C $(RUNTIME) push

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean: gc
	IMAGE=$(ACI)/aci-$(ACI_IMAGE) make -C $(RUNTIME) clean

fclean: clean
	IMAGE=$(ACI)/aci-$(BASE) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) clean

re: clean default
