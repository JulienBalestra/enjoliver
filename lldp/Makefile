CWD=$(shell pwd)

PROJECT=$(CWD)/..
RUNTIME=$(PROJECT)/runtime
DGR=$(RUNTIME)/dgr/dgr
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

BASE=base
DEBIAN=debian

LLDP_VERSION=0
LLDP=static-aci-lldp-$(LLDP_VERSION).aci

LLDP_IMAGE=static-aci-lldp:$(LLDP_VERSION)

RENDERS=$(RUNTIME)/renders
SQUASH=$(RENDERS)/squash_manifest.py
LLDP_RENDER=$(RENDERS)/lldp.render

default: $(LLDP)

$(BASE):
	@echo ENV IMAGE=$(ACI)/aci-$(BASE)
	IMAGE=$(ACI)/aci-$(BASE) make -C $(RUNTIME) install

$(DEBIAN): $(BASE)
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install

install: $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-lldp
	IMAGE=$(ACI)/aci-lldp make -C $(RUNTIME) install

$(LLDP): install
	$(RKT) --local-config=$(RUNTIME) image render $(LLDP_IMAGE) $(LLDP_RENDER) --overwrite
	chmod +r $(LLDP_RENDER)/manifest
	$(SQUASH) $(LLDP_RENDER)/manifest
	tar -C $(LLDP_RENDER) -cf $(LLDP) manifest rootfs
	file $(LLDP)
	$(RKT) --local-config=$(RUNTIME) fetch --insecure-options=all $(LLDP)

clean:
	IMAGE=$(CWD)/aci-lldp make -C $(RUNTIME) clean
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

fclean: clean
	IMAGE=$(ACI)/aci-$(BASE) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) clean
	rm -v $(LLDP) || true

re: clean default
