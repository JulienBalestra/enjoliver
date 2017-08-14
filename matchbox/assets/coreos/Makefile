VERSION=1409.6.0

SERVE=serve

CHANNEL=https://stable.release.core-os.net/amd64-usr
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
	curl -Lf https://coreos.com/security/image-signing-key/$(ASC) -o $(KEY)
	$(GPG) --logger-fd 1 --import < $(KEY)

$(KERNEL): $(KEY) $(VERSION)
	curl -Lf $(CHANNEL)/$(KERNEL) -o $(KERNEL)
	curl -Lf $(CHANNEL)/$(KERNEL).sig -o $(KERNEL).sig
	$(GPG) --logger-fd 1 --verify $(KERNEL).sig

$(INITRD): $(KEY) $(VERSION)
	curl -Lf $(CHANNEL)/$(INITRD) -o $(INITRD)
	curl -Lf $(CHANNEL)/$(INITRD).sig -o $(INITRD).sig
	$(GPG)  --logger-fd 1 --verify $(INITRD).sig

$(TEXT_VERSION): $(VERSION)
	curl -Lf $(CHANNEL)/$(TEXT_VERSION) -o $(TEXT_VERSION)

$(IMAGE):
	curl -Lf $(CHANNEL)/$(IMAGE) -o $(IMAGE)
	curl -Lf $(CHANNEL)/$(IMAGE).sig -o $(IMAGE).sig
	$(GPG) --logger-fd 1 --verify $(IMAGE).sig

ACI_PATH="../../../../../runtime/acserver.d/enjoliver.local"

unsquash: $(INITRD)
	VERSION=$(VERSION) ACI_PATH=$(ACI_PATH) ./unsquash.sh

clean:
	@rm -rfv $(VERSION) 2>&1 || true

$(SERVE):
	ln -vsf $(VERSION) $(SERVE)
	ln -vsf $(SERVE) current

fclean: clean
	@find * -maxdepth 1 -type d -exec rm -Rfv {} \;
	@rm -v $(SERVE) current || true

re: fclean default
