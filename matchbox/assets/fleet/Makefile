CWD=$(shell pwd)
SERVE=serve

VERSION=v0.11.8
FLEET_GITHUB=https://github.com/coreos/fleet/releases/download/$(VERSION)/fleet-$(VERSION)-linux-amd64.tar.gz

TARGET=$(VERSION)/fleet.tar.gz

default: $(TARGET)

$(TARGET):
	mkdir -pv $(VERSION)
	curl -fL $(FLEET_GITHUB) -o $(CWD)/$(TARGET)

clean:
	rm -v $(TARGET) || true

$(SERVE): $(TARGET)
	ln -svf $(VERSION) $(SERVE)

fclean: clean
	rm -Rfv $(VERSION) || true
	rm -v $(SERVE) || true

re: fclean $(TARGET)
