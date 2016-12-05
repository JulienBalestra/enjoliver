VERSION=1214.0.0

SERVE=serve

CHANNEL=https://alpha.release.core-os.net/amd64-usr
VMLINUZ=coreos_production_pxe.vmlinuz
CPIO=coreos_production_pxe_image.cpio.gz
TXT=version.txt
BZ2=coreos_production_image.bin.bz2

KERNEL=$(addprefix $(VERSION)/, $(VMLINUZ))
INITRD=$(addprefix $(VERSION)/, $(CPIO))
TEXT_VERSION=$(addprefix $(VERSION)/, $(TXT))
IMAGE=$(addprefix $(VERSION)/, $(BZ2))

ASC=CoreOS_Image_Signing_Key.asc

KEY=$(addprefix $(VERSION)/, $(ASC))
GPG=gpg

default: $(KEY) $(KERNEL) $(INITRD) $(TEXT_VERSION) $(IMAGE)

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
	$(GPG)  --logger-fd 1 --verify $(INITRD).sig

$(TEXT_VERSION): $(VERSION)
	curl -f $(CHANNEL)/$(TEXT_VERSION) -o $(TEXT_VERSION)

$(IMAGE): $(VERSION)
	curl -f $(CHANNEL)/$(IMAGE) -o $(IMAGE)
	curl -f $(CHANNEL)/$(IMAGE).sig -o $(IMAGE).sig
	$(GPG)  --logger-fd 1 --verify $(IMAGE).sig

clean:
	@rm -rfv $(VERSION) 2>&1 || true

$(SERVE):
	@ls -dF $(VERSION)
	ln -vs $(VERSION) $(SERVE)

fclean: clean
	@find * -maxdepth 1 -type d -exec rm -Rfv {} \;
	@rm -v $(SERVE) 2>&1 || true

re: fclean default