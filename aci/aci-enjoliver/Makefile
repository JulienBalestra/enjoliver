CWD=$(shell pwd)

PROJECT=$(CWD)/../..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

DEBIAN=debian
PYTHON=python
BUILDER_HYPERKUBE=builder-hyperkube
UPX=upx
GO=go
BUILDER_ENJOLIVER=builder-enjoliver
ENJOLIVER=enjoliver

default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$@
	IMAGE=$(ACI)/aci-$@ make -C $(RUNTIME) install

$(UPX): $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$@
	IMAGE=$(ACI)/aci-$@ make -C $(RUNTIME) install

$(GO): $(UPX)
	@echo ENV IMAGE=$(ACI)/aci-$@
	IMAGE=$(ACI)/aci-$@ make -C $(RUNTIME) install

$(BUILDER_HYPERKUBE): $(GO)
	@echo ENV IMAGE=$(ACI)/aci-$@
	IMAGE=$(ACI)/aci-$@ make -C $(RUNTIME) install

$(PYTHON): $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$@
	IMAGE=$(ACI)/aci-$@ make -C $(RUNTIME) install

$(BUILDER_ENJOLIVER): $(BUILDER_HYPERKUBE) $(PYTHON)
	@echo ENV IMAGE=$(ACI)/aci-$@
	IMAGE=$(ACI)/aci-$@ make -C $(RUNTIME) install

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
