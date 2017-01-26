CC=go
TARGET=discoveryC
FLAGS=-ldflags '-w'
CWD=$(shell pwd)

default: $(TARGET)

check:
	$(CC) test -v ./...

$(TARGET):
	GOPATH=$(GOPATH):$(CWD) CGO_ENABLED=0 GOOS=linux $(CC) build $(FLAGS) -o $(TARGET)

run: $(TARGET)
	./$(TARGET)

$(GODEP):
	go get github.com/tools/godep

restore: $(GODEP)
	godep restore

clean:
	rm -v $(TARGET) || true

re: clean $(TARGET)
