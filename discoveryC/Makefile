CC=go
TARGET=discoveryC
FLAGS=-ldflags '-w'
CWD=$(shell pwd)

default: $(TARGET)

check:
	GOPATH=$(CWD) $(CC) test -v ./

$(TARGET):
	GOPATH=$(CWD) CGO_ENABLED=0 GOOS=linux $(CC) build $(FLAGS) -o $(TARGET)

run: $(TARGET)
	./$(TARGET)

godep:
	go get -u github.com/tools/godep

restore: $(GODEP)
	godep restore

clean:
	rm -v $(TARGET) || true

re: clean $(TARGET)
