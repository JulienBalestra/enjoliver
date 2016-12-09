CHECK=check
CHECK_ASSETS=check_assets
CHECK_FAST=check_fast
CHECK_EUID=check_euid
CHECK_EUID_KVM_PLAYER=check_euid_kvm_player

default: help


help:
	@echo ----------------------
	@echo Setup:
	@echo sudo make apt
	@echo make submodules
	@echo sudo make acis
	@echo make assets
	@echo make validate
	@echo ----------------------
	@echo Testing:
	@echo make $(CHECK)
	@echo 
	@echo Skip: $(CHECK_ASSETS)
	@echo make $(CHECK_FAST)
	@echo
	@echo Only: $(CHECK_ASSETS)
	@echo make  $(CHECK_ASSETS)
	@echo
	@echo Ready for KVM:
	@echo sudo make $(CHECK_EUID_KVM_PLAYER)
	@echo
	@echo KVM - long:
	@echo sudo make $(CHECK_EUID)
	@echo ----------------------

apt:
	test $(shell id -u -r) -eq 0
	DEBIAN_FRONTEND=noninteractive INSTALL="-y" ./apt.sh


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
	make -C bootcfg/assets/cni fclean
	make -C bootcfg/assets/coreos fclean
	make -C bootcfg/assets/discoveryC fclean
	make -C bootcfg/assets/hyperkube fclean
	make -C bootcfg/assets/lldp fclean
	make -C bootcfg/assets/rkt fclean
	make -C bootcfg/assets/setup-network-environment fclean

$(CHECK):
	make -C discoveryC/ $(CHECK)
	make -C app/tests/ $(CHECK)

$(CHECK_FAST):
	make -C discoveryC/ $(CHECK)
	make -C app/tests/ $(CHECK_FAST)

$(CHECK_ASSETS):
	make -C app/tests/ $(CHECK_ASSETS)

$(CHECK_EUID):
	test $(shell id -u -r) -eq 0
	make -C app/tests/ $(CHECK_EUID)

$(CHECK_EUID_KVM_PLAYER):
	test $(shell id -u -r) -eq 0
	make -C app/tests/ $(CHECK_EUID_KVM_PLAYER)

submodules:
	git submodule init
	git submodule update

validate:
	@./validate.py

release: acis
	make -C release
