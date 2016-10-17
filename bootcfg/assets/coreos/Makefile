VERSION=1192.1.0
SERVE=serve

CHANNEL=https://alpha.release.core-os.net/amd64-usr
VMLINUZ=coreos_production_pxe.vmlinuz
CPIO=coreos_production_pxe_image.cpio.gz

KERNEL=$(addprefix $(VERSION)/, $(VMLINUZ))
INITRD=$(addprefix $(VERSION)/, $(CPIO))

ASC=CoreOS_Image_Signing_Key.asc

KEY=$(addprefix $(VERSION)/, $(ASC))
GPG=gpg

default: $(KEY) $(KERNEL) $(INITRD)

$(VERSION):
	test $(VERSION)
	mkdir -pv $(VERSION)

$(KEY): $(VERSION)
	curl -fs https://coreos.com/security/image-signing-key/$(ASC) -o $(KEY)
	$(GPG) --import < $(KEY)

$(KERNEL): $(KEY) $(VERSION)
	curl -fs $(CHANNEL)/$(KERNEL) -o $(KERNEL)
	curl -fs $(CHANNEL)/$(KERNEL).sig -o $(KERNEL).sig
	$(GPG) --verify $(PWD)/$(KERNEL).sig

$(INITRD): $(KEY) $(VERSION)
	curl -fs $(CHANNEL)/$(INITRD) -o $(INITRD)
	curl -fs $(CHANNEL)/$(INITRD).sig -o $(INITRD).sig
	$(GPG) --verify $(PWD)/$(KERNEL).sig

clean:
	@rm -rfv $(VERSION) || true

$(SERVE):
	@ls -dF $(VERSION)
	ln -vs $(VERSION) $(SERVE)

fclean: clean
	@find * -maxdepth 1 -type d -exec rm -Rfv {} \;
	@rm -v $(SERVE) || true

re: fclean default