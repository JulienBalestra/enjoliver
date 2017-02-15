SERVE=serve
PROJECT=lldp
ACI=static-aci-lldp-0.aci
TARGET=$(SERVE)/$(ACI)

default: $(TARGET)

$(SERVE):
	mkdir -vp $(SERVE)

$(TARGET): $(SERVE)
	cp -v ../../../$(PROJECT)/$(ACI) $(TARGET)

clean:
	rm -v $(TARGET) || true

fclean: clean
	rm -Rfv $(SERVE) || true

re: fclean $(TARGET)

