CHECK=check
CHECK_EUID=check_euid

default: submodules assets


assets:
	make -C bootcfg/assets/coreos
	make -C bootcfg/assets/coreos serve
	make -C bootcfg/assets/setup-network-environment
	make -C bootcfg/assets/setup-network-environment serve
	make -C bootcfg/assets/discoveryC

clean:
	make -C bootcfg/assets/coreos fclean
	make -C bootcfg/assets/setup-network-environment fclean
	make -C bootcfg/assets/discoveryC fclean

$(CHECK):
	make -C discoveryC/ $(CHECK)
	make -C app/tests/ $(CHECK)

$(CHECK_EUID):
	make -C app/tests/ $(CHECK_EUID)

submodules:
	git submodule init
	git submodule update