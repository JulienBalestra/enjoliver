CWD=$(shell pwd)

PROJECT=$(CWD)/..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci


DEBIAN=debian
GO=go
BUILDER_HYPERKUBE=builder-hyperkube
HEAPSTER=heapster


default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

$(GO): $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(GO)
	IMAGE=$(ACI)/aci-$(GO) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(GO) make -C $(RUNTIME) push

$(BUILDER_HYPERKUBE): $(GO)
	@echo ENV IMAGE=$(ACI)/aci-$(BUILDER_HYPERKUBE)
	IMAGE=$(ACI)/aci-$(BUILDER_HYPERKUBE) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

prepare: $(GO) $(BUILDER_HYPERKUBE)

install: prepare
	@echo ENV IMAGE=$(ACI)/aci-$(HEAPSTER)
	IMAGE=$(ACI)/aci-$(HEAPSTER) make -C $(RUNTIME) @^

test: install
	@echo ENV IMAGE=$(ACI)/aci-$(HEAPSTER)
	IMAGE=$(ACI)/aci-$(HEAPSTER) make -C $(RUNTIME) @^

push: test
	@echo ENV IMAGE=$(ACI)/aci-$(HEAPSTER)
	IMAGE=$(ACI)/aci-$(HEAPSTER) make -C $(RUNTIME) @^

gc:
	$(RKT) --local-config=$(RUNTIME) @^ --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image @^ --grace-period=0s

clean: gc
	IMAGE=$(ACI)/aci-$(HEAPSTER) make -C $(RUNTIME) @^

fclean: clean
	IMAGE=$(ACI)/aci-$(GO) make -C $(RUNTIME) clean
	IMAGE=$(ACI)/aci-$(BUILDER_HYPERKUBE) make -C $(RUNTIME) clean

re: clean default

re_quick:
	@echo ENV IMAGE=$(ACI)/aci-$(HEAPSTER)
	IMAGE=$(ACI)/aci-$(HEAPSTER) make -C $(RUNTIME) build
	IMAGE=$(ACI)/aci-$(HEAPSTER) make -C $(RUNTIME) push