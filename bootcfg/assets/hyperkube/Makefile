SERVE=serve
PROJECT=$(shell pwd)/../../..
HYPERKUBE=$(PROJECT)/hyperkube
BIN=hyperkube
ACI=static-aci-hyperkube-0.aci
TARGET_BIN=$(SERVE)/$(BIN)
TARGET_ACI=$(SERVE)/$(ACI)

default: $(TARGET_BIN) $(TARGET_ACI)

$(SERVE):
	mkdir -vp $(SERVE)

$(TARGET_BIN): $(SERVE)
	cp -v $(HYPERKUBE)/$(BIN) $(TARGET_BIN)

$(TARGET_ACI): $(SERVE)
	cp -v $(HYPERKUBE)/$(ACI) $(TARGET_ACI)

clean:
	rm -v $(TARGET_BIN) || true
	rm -v $(TARGET_ACI) || true

fclean: clean
	rm -Rfv $(SERVE) || true

re: fclean $(TARGET_BIN) $(TARGET_ACI)

