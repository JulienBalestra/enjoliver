CHECK=check
CHECK_EUID=check_euid

default: help


help:
	@echo ----------------------
	@echo Setup:
	@echo make submodules
	@echo sudo make acis
	@echo make assets
	@echo make validate
	@echo ----------------------
	@echo Testing:
	@echo make $(CHECK)
	@echo sudo make $(CHECK_EUID)
	@echo ----------------------

acis:
	test $(shell id -u -r) -eq 0
	make -C lldp
	make -C hyperkube

assets:
	make -C bootcfg/assets/coreos
	make -C bootcfg/assets/coreos serve
	make -C bootcfg/assets/setup-network-environment
	make -C bootcfg/assets/setup-network-environment serve
	make -C bootcfg/assets/rkt
	make -C bootcfg/assets/rkt serve
	make -C bootcfg/assets/cni
	make -C bootcfg/assets/cni serve
	# Self
	make -C bootcfg/assets/discoveryC
	@# Depends on .acis
	make -C bootcfg/assets/lldp
	make -C bootcfg/assets/hyperkube

clean:
	make -C bootcfg/assets/coreos fclean
	make -C bootcfg/assets/setup-network-environment fclean
	make -C bootcfg/assets/discoveryC fclean
	make -C bootcfg/assets/lldp fclean

$(CHECK):
	make -C discoveryC/ $(CHECK)
	make -C app/tests/ $(CHECK)

$(CHECK_EUID):
	test $(shell id -u -r) -eq 0
	make -C app/tests/ $(CHECK_EUID)

submodules:
	git submodule init
	git submodule update

validate:
	@./validate.py
