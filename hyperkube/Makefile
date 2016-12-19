CWD=$(shell pwd)

PROJECT=$(CWD)/..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

BASE=base
DEBIAN=debian

WS=workspace

BASE=base
DEBIAN=debian
BUILDER_K8S=builder-k8s
HYPERKUBE=$(WS)/hyperkube

default: $(HYPERKUBE)

$(BASE):
	@echo ENV IMAGE=$(ACI)/aci-$(BASE)
	IMAGE=$(ACI)/aci-$(BASE) make -C $(RUNTIME) install

$(DEBIAN): $(BASE)
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install

$(BUILDER_K8S): $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(BUILDER_K8S)
	IMAGE=$(ACI)/aci-$(BUILDER_K8S) make -C $(RUNTIME) install

$(HYPERKUBE): $(BUILDER_K8S) clean
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) run \
	    --interactive \
	    --insecure-options=all \
	    --net=host \
	    static-aci-builder-k8s \
	    --volume $(WS),kind=host,source=$(CWD)/$(WS) \
	    --mount volume=$(WS),target=/opt/$(WS) \
	    --exec /opt/$(WS)/build-hyperkube.sh ; \
	    $(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	ls -lh $(HYPERKUBE)

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean:
	rm -v $(HYPERKUBE) || true

fclean: clean gc
	IMAGE=$(CWD)/aci-$(BUILDER_K8S) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(BASE) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) clean

re: clean $(HYPERKUBE)