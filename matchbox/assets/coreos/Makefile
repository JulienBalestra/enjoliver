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

default: $(KEY) unsquash $(KERNEL) $(INITRD) $(TEXT_VERSION) $(IMAGE)

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

.ONESHELL:
unsquash: $(INITRD)
	cd $(VERSION) ;
	mkdir -p {squashfs,initrd} ;
	gunzip --force coreos_production_pxe_image.cpio.gz ;
	cd initrd
	cpio -id < ../coreos_production_pxe_image.cpio ;
	cd ../squashfs
	unsquashfs -no-progress ../initrd/usr.squashfs ;
	tar -C squashfs-root/ -xvf $(ACI_PATH)/etcd/etcd-3.2.5-linux-amd64.aci rootfs/usr/bin --strip 2 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp ;
	tar -C squashfs-root/ -xvf $(ACI_PATH)/vault/vault-0.8.0-linux-amd64.aci rootfs/usr/ --strip 2 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp ;
	tar -C squashfs-root/ -xvf $(ACI_PATH)/iproute2/iproute2-4.12.0-linux-amd64.aci rootfs/usr/bin --strip 2 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp ;
	tar -C squashfs-root/ -xvf $(ACI_PATH)/fleet/fleet-1.0.0-linux-amd64.aci rootfs/usr/bin --strip 2 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp ;
	tar -C squashfs-root/bin -xvf $(ACI_PATH)/hyperkube/hyperkube-1.7.2-linux-amd64.aci rootfs/ --strip 1 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp ;
	tar -C squashfs-root/ -xvf $(ACI_PATH)/rkt/rkt-1.27.0-linux-amd64.aci rootfs/usr  --keep-directory-symlink --strip 2 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp ;
	tar -C squashfs-root/ -xvf $(ACI_PATH)/cni/cni-0.5.2-linux-amd64.aci rootfs/usr --strip 2 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp ;
	mksquashfs   squashfs-root/ ../initrd/usr.squashfs -noappend -always-use-fragments ;
	cd ../initrd ;
	find .| cpio -o -H newc | gzip  > ../coreos_production_pxe_image.cpio.gz ;
	cd ../ ;
	rm -rf squashfs initrd coreos_production_pxe_image.cpio ;

clean:
	@rm -rfv $(VERSION) 2>&1 || true

$(SERVE):
	ln -vsf $(VERSION) $(SERVE)
	ln -vsf $(SERVE) current

fclean: clean
	@find * -maxdepth 1 -type d -exec rm -Rfv {} \;
	@rm -v $(SERVE) current || true

re: fclean default
