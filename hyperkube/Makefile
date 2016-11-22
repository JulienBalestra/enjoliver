CWD=$(shell pwd)

DGR=$(CWD)/../dgr
RKT=$(DGR)/rkt_dir/rkt
WS=workspace

BASE=base
DEBIAN=debian
BUILDER_K8S=builder-k8s
HYPERKUBE=$(WS)/hyperkube

default: $(HYPERKUBE)

$(BASE):
	@echo ENV IMAGE=$(CWD)/aci-$(BASE)
	IMAGE=$(DGR)/aci-$(BASE) make -C $(DGR) install

$(DEBIAN): $(BASE)
	@echo ENV IMAGE=$(CWD)/aci-$(DEBIAN)
	IMAGE=$(DGR)/aci-$(DEBIAN) make -C $(DGR) install

$(BUILDER_K8S): $(DEBIAN)
	@echo ENV IMAGE=$(CWD)/aci-$(BUILDER_K8S)
	IMAGE=$(CWD)/aci-$(BUILDER_K8S) make -C $(DGR) install

$(HYPERKUBE): $(BUILDER_K8S) clean
	$(RKT) --local-config=$(DGR) gc --grace-period=0s
	$(RKT) --local-config=$(DGR) run \
	    --interactive \
	    --insecure-options=all \
	    --net=host \
	    static-aci-builder-k8s \
	    --volume $(WS),kind=host,source=$(CWD)/$(WS) \
	    --mount volume=$(WS),target=/opt/$(WS) \
	    --exec /opt/$(WS)/build-hyperkube.sh ; \
	    $(RKT) --local-config=$(DGR) gc --grace-period=0s
	ls -lh $(HYPERKUBE)

gc:
	$(RKT) --local-config=$(DGR) gc --grace-period=0s
	$(RKT) --local-config=$(DGR) image gc --grace-period=0s

clean:
	rm -v $(HYPERKUBE) || true

fclean: clean gc
	IMAGE=$(CWD)/aci-$(BUILDER_K8S) make -C $(DGR) clean
	IMAGE=$(DGR)/aci-$(BASE) make -C $(DGR) clean
	IMAGE=$(DGR)/aci-$(DEBIAN) make -C $(DGR) clean

re: fclean $(HYPERKUBE)