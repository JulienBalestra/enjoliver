
SHELL=/bin/bash
IPXE=ipxe/src
CPU_NUM=$(shell grep -c '^processor' /proc/cpuinfo)
CPU_DIV=2
CPU_USAGE=$$(( $(CPU_NUM) / $(CPU_DIV) ))

ISO_RULE=ipxe.iso
ISO=ipxe/src/bin/$(ISO_RULE)

BUCKET=bbccoreos

EMBED_SCRIPT=$(shell pwd)/chain.ipxe

default: $(ISO_RULE)

re: fclean $(ISO_RULE)

$(IPXE):
	make -C ../ submodules

$(EMBED_SCRIPT):
	@echo "BOOTCFG_IP_PORT=$(BOOTCFG_IP_PORT)"
	@test $(BOOTCFG_IP_PORT)
	sed s/BOOTCFG_IP_PORT/$(BOOTCFG_IP_PORT)/g chain.ipxe.template > $(EMBED_SCRIPT)

$(ISO_RULE): $(IPXE) $(EMBED_SCRIPT)
	@file $(EMBED_SCRIPT)
	make -j$(CPU_USAGE) -C $(IPXE) bin/${ISO_RULE} EMBED=${EMBED_SCRIPT}
	@file $(shell pwd)/$(ISO)

clean: $(IPXE)
	rm -v $(ISO) || true

fclean: $(IPXE) clean
	rm -rf $(IPXE)/src/bin/*
