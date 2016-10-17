BINARY=setup-network-environment
VERSION=1.0.1
GITHUB_RELEASE=https://github.com/kelseyhightower/setup-network-environment/releases/download
TARGET=$(VERSION)/$(BINARY)
SHA=setup-network-environment.sha512
SERVE=serve

default: $(TARGET)

$(VERSION):
	test $(VERSION)
	mkdir -pv $(VERSION)

$(TARGET): $(VERSION)
	curl -Lfs $(GITHUB_RELEASE)/$(TARGET) -o $(TARGET)
	chmod 755 $(TARGET)
	sha512sum $(TARGET) > $(VERSION)/$(SHA)
	diff $(VERSION)-$(SHA) $(VERSION)/$(SHA)

clean:
	@rm -rfv $(VERSION) || true

$(SERVE):
	@ls -dF $(VERSION)
	ln -vs $(VERSION) $(SERVE)

fclean: clean
	@find * -maxdepth 1 -type d -exec rm -Rfv {} \;
	@rm -v $(SERVE) || true

re: fclean default