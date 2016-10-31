VERSION=1214.0.0

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
	curl -f https://coreos.com/security/image-signing-key/$(ASC) -o $(KEY)
	$(GPG) --logger-fd 1 --import < $(KEY)

$(KERNEL): $(KEY) $(VERSION)
	curl -f $(CHANNEL)/$(KERNEL) -o $(KERNEL)
	curl -f $(CHANNEL)/$(KERNEL).sig -o $(KERNEL).sig
	$(GPG) --logger-fd 1 --verify $(KERNEL).sig

$(INITRD): $(KEY) $(VERSION)
	curl -f $(CHANNEL)/$(INITRD) -o $(INITRD)
	curl -f $(CHANNEL)/$(INITRD).sig -o $(INITRD).sig
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