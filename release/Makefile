CWD=$(shell pwd)

PROJECT=$(CWD)/..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

DEBIAN=debian

ENJOLIVER_VERSION=0
ENJOLIVER=static-aci-enjoliver-$(ENJOLIVER_VERSION).aci

ENJOLIVER_IMAGE=static-aci-enjoliver:$(ENJOLIVER_VERSION)

RENDERS=$(RUNTIME)/renders
SQUASH=$(RENDERS)/squash_manifest.py
ENJOLIVER_RENDER=$(RENDERS)/enjoliver.render


default: $(ENJOLIVER)


$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install

install: $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-enjoliver
	IMAGE=$(ACI)/aci-enjoliver make -C $(RUNTIME) install

$(ENJOLIVER): install
	$(RKT) --local-config=$(RUNTIME) image render $(ENJOLIVER_IMAGE) $(ENJOLIVER_RENDER) --overwrite
	chmod +r $(ENJOLIVER_RENDER)/manifest
	$(SQUASH) $(ENJOLIVER_RENDER)/manifest
	tar -C $(ENJOLIVER_RENDER) -cf $(ENJOLIVER) manifest rootfs
	file $(ENJOLIVER)
	$(RKT) --local-config=$(RUNTIME) fetch --insecure-options=all $(ENJOLIVER)

clean:
	IMAGE=$(ACI)/aci-enjoliver make -C $(RUNTIME) clean
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

fclean: clean
	IMAGE=$(ACI)/aci-$(BASE) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) clean
	rm -v $(ENJOLIVER) || true

re: clean default
