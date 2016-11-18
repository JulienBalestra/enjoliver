
VERSION=v0.3.0
CNI_TAR=cni.tar.gz
SERVE=serve

GITHUB_TARGET="https://github.com/containernetworking/cni/releases/download/$(VERSION)/cni-$(VERSION).tgz"
TARGET=$(VERSION)/$(CNI_TAR)

default: $(TARGET)

$(VERSION):
	test $(VERSION)
	mkdir -pv $(VERSION)

$(TARGET): $(VERSION)
	curl -fL $(GITHUB_TARGET) -o $(TARGET)
	ls $(TARGET)
	tar -C $(VERSION) -xzvf $(TARGET)

clean:
	@rm -rfv $(VERSION) 2>&1 || true

$(SERVE): $(TARGET)
	@ls -dF $(VERSION)
	ln -vs $(VERSION) $(SERVE)

fclean: clean
	@rm -v $(SERVE) 2>&1 || true

re: fclean default