
SHELL=/bin/bash
IPXE=ipxe
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
	git submodule init $(IPXE)

$(ISO_RULE): $(IPXE)
	@file $(EMBED_SCRIPT)
	make -j$(CPU_USAGE) -C $(IPXE)/src bin/${ISO_RULE} EMBED=${EMBED_SCRIPT}
	@file $(shell pwd)/$(ISO)

clean: $(IPXE)
	rm -v $(ISO) || true

fclean: $(IPXE) clean
	rm -rf $(IPXE)/src/bin/*
