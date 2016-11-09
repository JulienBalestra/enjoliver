CHECK=check
CHECK_EUID=check_euid

default: submodules assets


acis:
	test $(shell id -u -r) -eq 0
	make -C lldp

assets:
	make -C bootcfg/assets/coreos
	make -C bootcfg/assets/coreos serve
	make -C bootcfg/assets/setup-network-environment
	make -C bootcfg/assets/setup-network-environment serve
	make -C bootcfg/assets/discoveryC
	make -C bootcfg/assets/lldp

clean:
	make -C bootcfg/assets/coreos fclean
	make -C bootcfg/assets/setup-network-environment fclean
	make -C bootcfg/assets/discoveryC fclean
	make -C bootcfg/assets/lldp fclean

$(CHECK):
	make -C discoveryC/ $(CHECK)
	make -C app/tests/ $(CHECK)

$(CHECK_EUID):
	make -C app/tests/ $(CHECK_EUID)

submodules:
	git submodule init
	git submodule update