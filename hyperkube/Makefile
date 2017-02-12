CWD=$(shell pwd)

PROJECT=$(CWD)/..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

BASE=base
DEBIAN=debian

HYPERKUBE_BIN=hyperkube
WS=workspace

DEBIAN=debian
BUILDER_K8S=builder-k8s

HYPERKUBE_VERSION=0
HYPERKUBE=static-aci-hyperkube-$(HYPERKUBE_VERSION).aci
HYPERKUBE_IMAGE=static-aci-hyperkube:$(HYPERKUBE_VERSION)

RENDERS=$(RUNTIME)/renders
SQUASH=$(RENDERS)/squash_manifest.py
HYPERKUBE_RENDER=$(RENDERS)/hyperkube.render


QUAY_HYPERKUBE_COREOS_IMAGE=quay.io/coreos/hyperkube
QUAY_HYPERKUBE_COREOS_VERSION=v1.5.1_coreos.0
QUAY_HYPERKUBE_COREOS=$(QUAY_HYPERKUBE_COREOS_IMAGE):$(QUAY_HYPERKUBE_COREOS_VERSION)
HYPERKUBE_COREOS=hyperkube-$(QUAY_HYPERKUBE_COREOS_VERSION)

default: $(HYPERKUBE)

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install

$(BUILDER_K8S): $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(BUILDER_K8S)
	IMAGE=$(ACI)/aci-$(BUILDER_K8S) make -C $(RUNTIME) install

$(HYPERKUBE_BIN): $(BUILDER_K8S) clean
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) run \
	    --interactive \
	    --insecure-options=all \
	    --net=host \
	    static-aci-builder-k8s \
	    --volume $(HYPERKUBE_BIN),kind=host,source=$(CWD) \
	    --mount volume=$(HYPERKUBE_BIN),target=/opt/$(HYPERKUBE_BIN) \
	    --exec /opt/$(HYPERKUBE_BIN)/$(WS)/build-hyperkube.sh ; \
	    $(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	ls -lh $(HYPERKUBE_BIN)

install: $(DEBIAN) $(HYPERKUBE_BIN)
	@echo ENV IMAGE=$(ACI)/aci-lldp
	IMAGE=$(ACI)/aci-hyperkube make -C $(RUNTIME) install

$(HYPERKUBE): install
	$(RKT) --local-config=$(RUNTIME) image render $(HYPERKUBE_IMAGE) $(HYPERKUBE_RENDER) --overwrite
	chmod +r $(HYPERKUBE_RENDER)/manifest
	$(SQUASH) $(HYPERKUBE_RENDER)/manifest
	tar -C $(HYPERKUBE_RENDER) -cf $(HYPERKUBE) manifest rootfs
	file $(HYPERKUBE)
	ls -lh $(HYPERKUBE)

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean:
	rm -v $(HYPERKUBE_BIN) || true
	rm -v $(HYPERKUBE) || true

fclean: clean gc
	IMAGE=$(CWD)/aci-$(BUILDER_K8S) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(BASE) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) clean

re: clean $(HYPERKUBE)
