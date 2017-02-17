CWD=$(shell pwd)

PROJECT=$(CWD)/..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

HYPERKUBE_BIN=hyperkube

DEBIAN=debian
BUILDER_K8S=builder-k8s
HYPERKUBE=hyperkube


default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

$(BUILDER_K8S): $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(BUILDER_K8S)
	IMAGE=$(ACI)/aci-$(BUILDER_K8S) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

$(HYPERKUBE_BIN): $(BUILDER_K8S)
	@echo ENV IMAGE=$(ACI)/aci-hyperkube
	IMAGE=$(ACI)/aci-hyperkube make -C $(RUNTIME) build
	ls -lh $(HYPERKUBE_BIN)

install: $(DEBIAN) $(BUILDER_K8S)
	@echo ENV IMAGE=$(ACI)/aci-hyperkube
	IMAGE=$(ACI)/aci-hyperkube make -C $(RUNTIME) install

test: install
	@echo ENV IMAGE=$(ACI)/aci-hyperkube
	IMAGE=$(ACI)/aci-hyperkube make -C $(RUNTIME) push

push: test
	@echo ENV IMAGE=$(ACI)/aci-hyperkube
	IMAGE=$(ACI)/aci-hyperkube make -C $(RUNTIME) push

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean: gc
	rm -v $(HYPERKUBE_BIN) || true
	IMAGE=$(ACI)/aci-hyperkube make -C $(RUNTIME) clean

fclean: clean
	IMAGE=$(CWD)/aci-$(BUILDER_K8S) make -C $(RUNTIME) clean

re: clean $(HYPERKUBE)
