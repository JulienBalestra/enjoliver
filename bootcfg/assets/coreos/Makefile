VERSION=current

STABLE=https://stable.release.core-os.net/amd64-usr
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
	curl -fs $(STABLE)/$(KERNEL) -o $(KERNEL)
	curl -fs $(STABLE)/$(KERNEL).sig -o $(KERNEL).sig
	$(GPG) --verify $(PWD)/$(KERNEL).sig

$(INITRD): $(KEY) $(VERSION)
	curl -fs $(STABLE)/$(INITRD) -o $(INITRD)
	curl -fs $(STABLE)/$(INITRD).sig -o $(INITRD).sig
	$(GPG) --verify $(PWD)/$(KERNEL).sig

clean:
	@rm -rfv $(VERSION) || true

re: clean default