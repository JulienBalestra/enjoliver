CC=go
TARGET=discoveryC

check:
	$(CC) test -v ./...

$(TARGET):
	$(CC) build -o $(TARGET)

run: $(TARGET)
	./$(TARGET)

clean:
	rm -v $(TARGET)

re: clean $(TARGET)
