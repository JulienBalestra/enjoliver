CWD=$(shell pwd)

PROJECT=$(CWD)/..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

DEBIAN=debian
BUILDER_K8S=builder-k8s
BUILDER_ENJOLIVER=builder-enjoliver

default: test


$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install

$(BUILDER_K8S): $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(BUILDER_K8S)
	IMAGE=$(ACI)/aci-$(BUILDER_K8S) make -C $(RUNTIME) install

$(BUILDER_ENJOLIVER): $(BUILDER_K8S)
	@echo ENV IMAGE=$(ACI)/aci-$(BUILDER_K8S)
	IMAGE=$(ACI)/aci-$(BUILDER_ENJOLIVER) make -C $(RUNTIME) install

build: $(BUILDER_ENJOLIVER)
	@echo ENV IMAGE=$(ACI)/aci-enjoliver
	IMAGE=$(ACI)/aci-enjoliver make -C $(RUNTIME) build

install: $(BUILDER_ENJOLIVER)
	@echo ENV IMAGE=$(ACI)/aci-enjoliver
	IMAGE=$(ACI)/aci-enjoliver make -C $(RUNTIME) install

test: install
	@echo ENV IMAGE=$(ACI)/aci-enjoliver
	IMAGE=$(ACI)/aci-enjoliver make -C $(RUNTIME) test

push: test
	@echo ENV IMAGE=$(ACI)/aci-enjoliver
	IMAGE=$(ACI)/aci-enjoliver make -C $(RUNTIME) push

clean:
	IMAGE=$(ACI)/aci-enjoliver make -C $(RUNTIME) clean
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

fclean: clean
	IMAGE=$(ACI)/aci-$(BASE) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) clean
	rm -v $(ENJOLIVER) || true

re: clean default
