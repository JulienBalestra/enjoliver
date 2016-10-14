STABLE=https://stable.release.core-os.net/amd64-usr/current

KERNEL=coreos_production_pxe.vmlinuz
INITRD=coreos_production_pxe_image.cpio.gz
PGP=CoreOS_Image_Signing_Key.asc

default: $(PGP) $(KERNEL) $(INITRD)

$(KERNEL): $(PGP)
	curl -Ofs $(STABLE)/$(KERNEL)
	curl -Ofs $(STABLE)/$(KERNEL).sig
	gpg2 --status-fd 1 --no-default-keyring --keyring $(PWD)/$(PGP).gpg \
		--trust-model always --verify $(KERNEL).sig

$(INITRD): $(PGP)
	curl -Ofs $(STABLE)/$(INITRD)
	curl -Ofs $(STABLE)/$(INITRD).sig
	gpg2 --status-fd 1 --no-default-keyring --keyring $(PWD)/$(PGP).gpg \
		--trust-model always --verify $(INITRD).sig

clean:
	@rm -v $(KERNEL) || true
	@rm -v $(KERNEL).sig || true
	@rm -v $(INITRD) || true
	@rm -v $(INITRD).sig || true
	@rm -v $(PGP) || true
	@rm -v $(PGP).gpg || true

$(PGP):
	curl -Ofs https://coreos.com/security/image-signing-key/$(PGP)
	gpg2 -o $(PGP).gpg --dearmor $(PGP)

re: clean default