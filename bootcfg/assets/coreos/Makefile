VERSION=current
STABLE=https://stable.release.core-os.net/amd64-usr


KERNEL=$(VERSION)/coreos_production_pxe.vmlinuz
INITRD=$(VERSION)/coreos_production_pxe_image.cpio.gz
ASC=$(VERSION)/CoreOS_Image_Signing_Key.asc
GPG=gpg

default: $(ASC) $(KERNEL) $(INITRD)

$(KERNEL): $(ASC)
	mkdir -pv $(VERSION)
	curl -fs $(STABLE)/$(KERNEL) -o $(KERNEL)
	curl -fs $(STABLE)/$(KERNEL).sig -o $(KERNEL).sig
	$(GPG) --verify $(PWD)/$(KERNEL).sig

$(INITRD): $(PGP)
	mkdir -pv $(VERSION)
	curl -fs $(STABLE)/$(INITRD) -o $(INITRD)
	curl -fs $(STABLE)/$(INITRD).sig -o $(INITRD)
	$(GPG) --verify $(PWD)/$(KERNEL).sig

clean:
	@rm -rfv $(VERSION) || true

$(ASC):
	mkdir -pv $(VERSION)
	curl -fs https://coreos.com/security/image-signing-key/$(PGP) -o $(ASC)
	$(GPG) --import < $(ASC) || true

re: clean default