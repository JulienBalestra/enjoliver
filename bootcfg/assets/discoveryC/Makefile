SERVE=serve
PROJECT=discoveryC
BIN=discoveryC
TARGET=$(SERVE)/$(BIN)

default: $(TARGET)

$(SERVE):
	mkdir -vp $(SERVE)

$(TARGET): $(SERVE)
	make -C ../../../$(PROJECT) re
	cp -v ../../../$(PROJECT)/$(BIN) $(TARGET)

clean:
	rm -v $(TARGET) || true

fclean: clean
	rm -Rfv $(SERVE) || true

re: fclean $(TARGET)

