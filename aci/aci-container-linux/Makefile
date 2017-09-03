CWD=$(shell pwd)

PROJECT=$(CWD)/../..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci

UPX=upx
TARGET=container-linux

default: install

$(UPX):
	@echo ENV IMAGE=$(ACI)/aci-$@
	IMAGE=$(ACI)/aci-$@ make -C $(RUNTIME) install

install: $(UPX)
	@echo ENV IMAGE=$(ACI)/aci-$(TARGET)
	IMAGE=$(ACI)/aci-$(TARGET) make -C $(RUNTIME) install

test: install
	@echo ENV IMAGE=$(ACI)/aci-$(TARGET)
	IMAGE=$(ACI)/aci-$(TARGET) make -C $(RUNTIME) test

push: test
	@echo ENV IMAGE=$(ACI)/aci-$(TARGET)
	IMAGE=$(ACI)/aci-$(TARGET) make -C $(RUNTIME) push

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean: gc
	IMAGE=$(ACI)/aci-$(TARGET) make -C $(RUNTIME) gc
	IMAGE=$(ACI)/aci-$(TARGET) make -C $(RUNTIME) clean

re: clean default
