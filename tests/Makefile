BIN=bin
TARGET=$(BIN)/bootcfg
RELEASE=https://github.com/coreos/coreos-baremetal/releases/download/v0.4.0/coreos-baremetal-v0.4.0-linux-amd64.tar.gz

default: $(TARGET)

$(TARGET):
	mkdir -pv $(BIN)
	curl -Lf $(RELEASE) -o $(TARGET).tar.gz
	tar -C $(BIN) -xzvf $(TARGET).tar.gz --strip-components=1
	file $(TARGET)

clean:
	@rm -v $(TARGET).tar.gz

fclean:
	@rm -Rf $(BIN)

check: $(TARGET)
	python -m unittest discover .

re: fclean default
