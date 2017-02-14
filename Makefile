CWD=$(shell pwd)
CHECK=check
CHECK_EUID=check_euid
CHECK_EUID_KVM_PLAYER=check_euid_kvm_player

default: help

help:
	@echo ----------------------
	@echo Prepare:
	@echo sudo make apt
	@echo ----------------------
	@echo Setup:
	@echo make submodules
	@echo make runner
	@echo sudo make acis
	@echo make assets
	@echo make validate
	@echo
	@echo All in one:
	@echo sudo MY_USER= setup
	@echo ----------------------
	@echo Testing:
	@echo make $(CHECK)
	@echo
	@echo Ready for KVM:
	@echo sudo make $(CHECK_EUID_KVM_PLAYER)
	@echo
	@echo KVM - long:
	@echo sudo make $(CHECK_EUID)
	@echo ----------------------
	@echo Release:
	@echo sudo make release_aci
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
	make -C bootcfg/assets/rkt
	make -C bootcfg/assets/rkt serve
	make -C bootcfg/assets/etcd
	make -C bootcfg/assets/etcd serve
	make -C bootcfg/assets/cni
	make -C bootcfg/assets/cni serve
	make -C bootcfg/assets/fleet
	make -C bootcfg/assets/fleet serve
	# Self
	make -C bootcfg/assets/discoveryC
	# Depends on .acis
	make -C bootcfg/assets/lldp
	make -C bootcfg/assets/hyperkube

clean: check_clean
	make -C bootcfg/assets/cni fclean
	make -C bootcfg/assets/coreos fclean
	make -C bootcfg/assets/discoveryC fclean
	make -C bootcfg/assets/hyperkube fclean
	make -C bootcfg/assets/lldp fclean
	make -C bootcfg/assets/rkt fclean

check_clean:
	make -C app/tests/ fclean

$(CHECK):
	make -C discoveryC/ $(CHECK)
	make -C app/tests/ $(CHECK)

$(CHECK_EUID): validate
	test $(shell id -u -r) -eq 0
	make -C app/tests/ $(CHECK_EUID)

$(CHECK_EUID_KVM_PLAYER):
	test $(shell id -u -r) -eq 0
	make -C app/tests/ $(CHECK_EUID_KVM_PLAYER)

submodules:
	git submodule update --init --recursive

validate:
	@./validate.py

runner:
	make -C runtime

release_aci:
	make -C release

front:
	make -C app/static

config:
	mkdir -pv $(HOME)/.config/enjoliver
	touch $(HOME)/.config/enjoliver/config.env
	touch $(HOME)/.config/enjoliver/config.json

setup:
	echo "Need MY_USER for non root operations"
	test $(MY_USER)
	test $(shell id -u -r) -eq 0
	su - $(MY_USER) -c "make -C $(CWD) submodules"
	su - $(MY_USER) -c "make -C $(CWD) runner"
	su - $(MY_USER) -c "make -C $(CWD) front"
	make -C $(CWD) acis
	su - $(MY_USER) -c "make -C $(CWD) assets"
	su - $(MY_USER) -c "make -C $(CWD) validate"
	su - $(MY_USER) -c "make -C $(CWD) config"
