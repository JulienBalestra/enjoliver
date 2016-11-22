SERVE=serve
PROJECT=hyperkube
WS=$(PROJECT)/workspace
BIN=hyperkube
TARGET=$(SERVE)/$(BIN)

default: $(TARGET)

$(SERVE):
	mkdir -vp $(SERVE)

$(TARGET): $(SERVE)
	cp -v ../../../$(WS)/$(BIN) $(TARGET)

clean:
	rm -v $(TARGET) || true

fclean: clean
	rm -Rfv $(SERVE) || true

re: fclean $(TARGET)

