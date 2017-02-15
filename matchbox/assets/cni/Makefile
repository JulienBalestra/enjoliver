CWD=$(shell pwd)
PROJECT=$(CWD)/../../..

CNI_TAR=cni.tar.gz
CNI_TARGET=$(PROJECT)/cni/cni.tar.gz
SERVE=serve
SERVE_CNI=$(SERVE)/$(CNI_TAR)

TARGET=$(VERSION)/$(CNI_TAR)

default: $(CNI_TARGET)

$(CNI_TARGET):
	cd $(PROJECT)/cni && \
		./build && \
		tar -czvf $(CNI_TAR) ./bin

clean:
	@rm -v $(CNI_TARGET) 2>&1 || true

$(SERVE): $(CNI_TARGET)
	ls -l $(CNI_TARGET)
	mkdir -pv $(SERVE)
	cp -v $(CNI_TARGET) $(SERVE_CNI)

fclean: clean
	@rm -Rfv $(SERVE) 2>&1 || true

re: fclean default