CWD=$(shell pwd)

PROJECT=$(CWD)/..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

DEBIAN=debian

LLDP=lldp


default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

install: $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-lldp
	IMAGE=$(ACI)/aci-$(LLDP) make -C $(RUNTIME) install

push: $(DEBIAN)
	IMAGE=$(ACI)/aci-$(LLDP) make -C $(RUNTIME) push

clean:
	rm -v $(LLDP) || true

fclean: clean
	IMAGE=$(ACI)/aci-$(BASE) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) clean
	IMAGE=$(CWD)/aci-lldp make -C $(RUNTIME) clean
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

re: clean default
