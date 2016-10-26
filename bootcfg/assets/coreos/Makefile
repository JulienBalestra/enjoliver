VERSION=1122.3.0

SERVE=serve

CHANNEL=https://stable.release.core-os.net/amd64-usr
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
	$(GPG) --logger-fd 1 --import < $(KEY)

$(KERNEL): $(KEY) $(VERSION)
	curl -fs $(CHANNEL)/$(KERNEL) -o $(KERNEL)
	curl -fs $(CHANNEL)/$(KERNEL).sig -o $(KERNEL).sig
	$(GPG) --logger-fd 1 --verify $(KERNEL).sig

$(INITRD): $(KEY) $(VERSION)
	curl -fs $(CHANNEL)/$(INITRD) -o $(INITRD)
	curl -fs $(CHANNEL)/$(INITRD).sig -o $(INITRD).sig
	$(GPG)  --logger-fd 1 --verify $(KERNEL).sig

clean:
	@rm -rfv $(VERSION) 2>&1 || true

$(SERVE):
	@ls -dF $(VERSION)
	ln -vs $(VERSION) $(SERVE)

fclean: clean
	@find * -maxdepth 1 -type d -exec rm -Rfv {} \;
	@rm -v $(SERVE) 2>&1 || true

re: fclean default