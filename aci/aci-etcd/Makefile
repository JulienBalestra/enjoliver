CWD=$(shell pwd)

PROJECT=$(CWD)/../../
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci


DEBIAN=debian
ETCD=etcd


default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

build: $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(ETCD)
	IMAGE=$(ACI)/aci-$(ETCD) make -C $(RUNTIME) build

test: build
	@echo ENV IMAGE=$(ACI)/aci-$(ETCD)
	IMAGE=$(ACI)/aci-$(ETCD) make -C $(RUNTIME) test

push: test
	@echo ENV IMAGE=$(ACI)/aci-$(ETCD)
	IMAGE=$(ACI)/aci-$(ETCD) make -C $(RUNTIME) push

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean: gc
	IMAGE=$(ACI)/aci-$(ETCD) make -C $(RUNTIME) clean

fclean: clean

re: clean default
