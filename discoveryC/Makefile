CC=go
TARGET=discoveryC
FLAGS=-ldflags '-w'

default: $(TARGET)

check:
	$(CC) test -v ./...

$(TARGET):
	CGO_ENABLED=0 GOOS=linux $(CC) build $(FLAGS) -o $(TARGET)

run: $(TARGET)
	./$(TARGET)

clean:
	rm -v $(TARGET) || true

re: clean $(TARGET)
