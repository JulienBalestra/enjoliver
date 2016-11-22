CWD=$(shell pwd)

DGR=$(CWD)/../dgr
RKT=$(DGR)/rkt_dir/rkt

BASE=base
DEBIAN=debian

LLDP_VERSION=0
LLDP=static-aci-lldp-$(LLDP_VERSION).aci

LLDP_IMAGE=static-aci-lldp:$(LLDP_VERSION)

RENDER=lldp.render

default: $(LLDP)

$(BASE):
	@echo ENV IMAGE=$(CWD)/aci-lldp
	IMAGE=$(DGR)/aci-$(BASE) make -C $(DGR) install

$(DEBIAN): $(BASE)
	@echo ENV IMAGE=$(CWD)/aci-lldp
	IMAGE=$(DGR)/aci-$(DEBIAN) make -C $(DGR) install

$(LLDP): $(DEBIAN)
	@echo ENV IMAGE=$(CWD)/aci-lldp
	IMAGE=$(CWD)/aci-lldp make -C $(DGR) install
	$(RKT) --local-config=$(DGR) image render $(LLDP_IMAGE) $(RENDER) --overwrite
	chmod +rx $(RENDER)/manifest
	$(CWD)/squash_manifest.py
	tar -C $(RENDER) -cf $(LLDP) manifest rootfs
	file $(LLDP)
	$(RKT) --local-config=$(DGR) fetch --insecure-options=all $(LLDP)

clean:
	IMAGE=$(CWD)/aci-lldp make -C $(DGR) clean
	$(RKT) --local-config=$(DGR) image gc --grace-period=0s

fclean: clean
	IMAGE=$(DGR)/aci-$(BASE) make -C $(DGR) clean
	IMAGE=$(DGR)/aci-$(DEBIAN) make -C $(DGR) clean
	rm -Rf $(RENDER) || true
	rm -v $(LLDP) || true