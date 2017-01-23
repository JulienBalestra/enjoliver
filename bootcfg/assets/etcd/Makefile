CWD=$(shell pwd)
SERVE=serve

VERSION=v3.1.0
ETCD_GITHUB=https://github.com/coreos/etcd/releases/download/$(VERSION)/etcd-$(VERSION)-linux-amd64.tar.gz

TARGET=$(VERSION)/etcd.tar.gz

default: $(TARGET)

$(TARGET):
	mkdir -pv $(VERSION)
	curl -fL $(ETCD_GITHUB) -o $(CWD)/$(TARGET)

clean:
	rm -v $(TARGET) || true

$(SERVE): $(TARGET)
	ln -sv $(VERSION) $(SERVE)

fclean: clean
	rm -Rfv $(VERSION) || true
	rm -v $(SERVE) || true

re: fclean $(TARGET)
