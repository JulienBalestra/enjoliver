CWD=$(shell pwd)

PROJECT=$(CWD)/../..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

DEBIAN=debian

TARGET=ubuntu


default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$@
	IMAGE=$(ACI)/aci-$@ make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$@ make -C $(RUNTIME) push

install: $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(TARGET)
	IMAGE=$(ACI)/aci-$(TARGET) make -C $(RUNTIME) install

push: $(DEBIAN)
	IMAGE=$(ACI)/aci-$(TARGET) make -C $(RUNTIME) push

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean: gc
	IMAGE=$(ACI)/aci-$(TARGET) make -C $(RUNTIME) clean

fclean: clean
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) clean

re: clean default
