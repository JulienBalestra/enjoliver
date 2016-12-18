SHELL=/bin/bash
IPXE=ipxe/src
CPU_NUM=$(shell grep -c '^processor' /proc/cpuinfo)
CPU_DIV=2
CPU_USAGE=$$(( $(CPU_NUM) / $(CPU_DIV) ))

ISO_RULE=ipxe.iso
ISO=ipxe/src/bin/$(ISO_RULE)

KKK_RULE=undionly.kkkpxe
KKK=ipxe/src/bin/$(KKK_RULE)

EMBED_SCRIPT=$(shell pwd)/chain.ipxe

default: $(KKK_RULE)

re: fclean $(ISO_RULE)

$(IPXE):
	make -C ../ submodules

$(EMBED_SCRIPT):
	@echo "CHAIN_IP_PORT=$(CHAIN_IP_PORT)"
	test $(CHAIN_IP_PORT)
	sed s/CHAIN_IP_PORT/$(CHAIN_IP_PORT)/g chain.ipxe.template > $(EMBED_SCRIPT)
	@rm -v $(ISO) || true

$(ISO_RULE): $(IPXE) $(EMBED_SCRIPT)
	@file $(EMBED_SCRIPT)
	make -j$(CPU_USAGE) -C $(IPXE) bin/${ISO_RULE} EMBED=${EMBED_SCRIPT}
	@file $(shell pwd)/$(ISO)

$(KKK_RULE): $(IPXE) $(EMBED_SCRIPT)
	make -j$(CPU_USAGE) -C $(IPXE) bin/${KKK_RULE} EMBED=${EMBED_SCRIPT}
	@file $(shell pwd)/$(KKK)

clean: $(IPXE)
	@rm -v $(EMBED_SCRIPT) || true
	@rm -v $(ISO) || true
	@rm -v $(KKK) || true

fclean: $(IPXE) clean
	rm -rf $(IPXE)/src/bin/*
