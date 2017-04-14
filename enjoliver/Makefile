CWD=$(shell pwd)

PROJECT=$(CWD)/..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

DEBIAN=debian
PYTHON=python
BUILDER_HYPERKUBE=builder-hyperkube
GO=go
BUILDER_ENJOLIVER=builder-enjoliver
ENJOLIVER=enjoliver

default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install

$(GO): $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(GO)
	IMAGE=$(ACI)/aci-$(GO) make -C $(RUNTIME) install

$(BUILDER_HYPERKUBE): $(GO)
	@echo ENV IMAGE=$(ACI)/aci-$(BUILDER_HYPERKUBE)
	IMAGE=$(ACI)/aci-$(BUILDER_HYPERKUBE) make -C $(RUNTIME) install

$(PYTHON): $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(PYTHON)
	IMAGE=$(ACI)/aci-$(PYTHON) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(PYTHON) make -C $(RUNTIME) test

$(BUILDER_ENJOLIVER): $(BUILDER_HYPERKUBE) $(PYTHON)
	@echo ENV IMAGE=$(ACI)/aci-$(BUILDER_ENJOLIVER)
	IMAGE=$(ACI)/aci-$(BUILDER_ENJOLIVER) make -C $(RUNTIME) install

build: $(BUILDER_ENJOLIVER)
	@echo ENV IMAGE=$(ACI)/aci-$(ENJOLIVER)
	IMAGE=$(ACI)/aci-$(ENJOLIVER) make -C $(RUNTIME) build

install: build
	@echo ENV IMAGE=$(ACI)/aci-$(ENJOLIVER)
	IMAGE=$(ACI)/aci-$(ENJOLIVER) make -C $(RUNTIME) install

test: install
	@echo ENV IMAGE=$(ACI)/aci-$(ENJOLIVER)
	IMAGE=$(ACI)/aci-$(ENJOLIVER) make -C $(RUNTIME) test

push: test
	@echo ENV IMAGE=$(ACI)/aci-$(ENJOLIVER)
	IMAGE=$(ACI)/aci-$(ENJOLIVER) make -C $(RUNTIME) push

clean:
	IMAGE=$(ACI)/aci-$(ENJOLIVER) make -C $(RUNTIME) clean

fclean: clean
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(BUILDER_HYPERKUBE) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(BUILDER_ENJOLIVER) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(ENJOLIVER) make -C $(RUNTIME) clean
	rm -v $(ENJOLIVER) || true

re: clean default
