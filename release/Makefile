CWD=$(shell pwd)

DGR=$(CWD)/../dgr
RKT=$(DGR)/rkt_dir/rkt

BASE=base
DEBIAN=debian

ENJOLIVER_VERSION=0
ENJOLIVER=static-aci-enjoliver-$(ENJOLIVER_VERSION).aci

ENJOLIVER_IMAGE=static-aci-enjoliver:$(ENJOLIVER_VERSION)

RENDER=enjoliver.render


default: $(ENJOLIVER)

$(BOOTCFG):
	mkdir -pv $(BOOTCFG_DIR) $(BOOTCFG_INSTALL)
	curl -Lf $(BOOTCFG_RELEASE) -o $(BOOTCFG_INSTALL)/bootcfg.tar.gz
	tar -C $(BOOTCFG_INSTALL) -xzf $(BOOTCFG_INSTALL)/bootcfg.tar.gz --strip-components=1
	cp -v $(BOOTCFG_INSTALL)/bootcfg $(BOOTCFG)
	rm -Rfv $(BOOTCFG_INSTALL)

$(BASE):
	@echo ENV IMAGE=$(CWD)/aci-$(BASE)
	IMAGE=$(DGR)/aci-$(BASE) make -C $(DGR) install

$(DEBIAN): $(BASE)
	@echo ENV IMAGE=$(CWD)/aci-$(DEBIAN)
	IMAGE=$(DGR)/aci-$(DEBIAN) make -C $(DGR) install

$(ENJOLIVER): $(DEBIAN) $(BOOTCFG)
	@echo ENV IMAGE=$(CWD)/aci-enjoliver
	IMAGE=$(CWD)/aci-enjoliver make -C $(DGR) install
	$(RKT) --local-config=$(DGR) image render $(ENJOLIVER_IMAGE) $(RENDER) --overwrite
	chmod +rx $(RENDER)/manifest
	$(CWD)/squash_manifest.py
	tar -C $(RENDER) -cf $(ENJOLIVER) manifest rootfs
	file $(ENJOLIVER)
	ls -lh $(CWD)/$(ENJOLIVER)
	$(RKT) --local-config=$(DGR) fetch --insecure-options=all $(ENJOLIVER)

clean:
	rm -Rfv $(RENDER) aci-enjoliver/target || true
	IMAGE=$(CWD)/aci-enjoliver make -C $(DGR) clean
	$(RKT) --local-config=$(DGR) image gc --grace-period=0s
	$(RKT) --local-config=$(DGR) gc --grace-period=0s
	rm -v db.sqlite db.sqlite-*bak || true

fclean: clean
	IMAGE=$(DGR)/aci-$(BASE) make -C $(DGR) clean
	IMAGE=$(DGR)/aci-$(DEBIAN) make -C $(DGR) clean
	rm -Rf $(RENDER) || true
	rm -v $(ENJOLIVER) || true

re: clean default

run_gunicorn:
	$(RKT) --local-config=$(DGR) image cat-manifest static-aci-enjoliver || \
		$(RKT) --local-config=$(DGR) fetch --insecure-options=all $(ENJOLIVER)
	$(RKT) --local-config=$(DGR) \
		run --interactive \
		--net=host \
		--set-env-file=$(ENJOLIVER_EF) \
		--volume=enjoliver-path,kind=host,source=$(CWD)/var_lib_enjoliver,readOnly=false \
		--volume=bootcfg-groups,kind=host,source=$(CWD)/var_lib_bootcfg/groups,readOnly=false \
		--volume=bootcfg-profiles,kind=host,source=$(CWD)/var_lib_bootcfg/profiles,readOnly=false \
		static-aci-enjoliver \
		--exec /usr/local/bin/gunicorn -- \
		--chdir /opt/enjoliver/app \
		--log-level debug \
		-b 0.0.0.0:5000 \
		api:application

run_bootcfg:
	$(RKT) --local-config=$(DGR) image cat-manifest static-aci-enjoliver || \
		$(RKT) --local-config=$(DGR) fetch --insecure-options=all $(ENJOLIVER)
	$(RKT) --local-config=$(DGR) \
		run --interactive \
		--net=host \
		--set-env-file=$(ENJOLIVER_EF) \
		--volume=enjoliver-path,kind=host,source=$(CWD)/var_lib_enjoliver,readOnly=false \
		--volume=bootcfg-groups,kind=host,source=$(CWD)/var_lib_bootcfg/groups,readOnly=false \
		--volume=bootcfg-profiles,kind=host,source=$(CWD)/var_lib_bootcfg/profiles,readOnly=false \
		static-aci-enjoliver \
		--exec /usr/bin/bootcfg -- \
		-log-level debug \
		-address 0.0.0.0:8080

run_all_in_one:
	$(RKT) --local-config=$(DGR) image cat-manifest static-aci-enjoliver || \
		$(RKT) --local-config=$(DGR) fetch --insecure-options=all $(ENJOLIVER)
	$(RKT) --local-config=$(DGR) \
		run --interactive \
		--net=host \
		--set-env-file=$(ENJOLIVER_EF) \
		--volume=enjoliver-path,kind=host,source=$(CWD)/var_lib_enjoliver,readOnly=false \
		--volume=bootcfg-groups,kind=host,source=$(CWD)/var_lib_bootcfg/groups,readOnly=false \
		--volume=bootcfg-profiles,kind=host,source=$(CWD)/var_lib_bootcfg/profiles,readOnly=false \
		static-aci-enjoliver \
		--exec /opt/enjoliver/app/plans/all_in_one.py
