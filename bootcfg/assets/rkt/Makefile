CWD=$(shell pwd)
SERVE=serve

VERSION=v1.22.0
RKT_GITHUB=https://github.com/coreos/rkt/releases/download/$(VERSION)/rkt-$(VERSION).tar.gz

TARGET=$(VERSION)/rkt.tar.gz

default: $(TARGET)

$(TARGET):
	mkdir -pv $(VERSION)
	curl -fL $(RKT_GITHUB) -o $(CWD)/$(TARGET)

clean:
	rm -v $(TARGET) || true

$(SERVE): $(TARGET)
	ln -sv $(VERSION) $(SERVE)

fclean: clean
	rm -Rfv $(VERSION) || true
	rm -v $(SERVE) || true

re: fclean $(TARGET)
