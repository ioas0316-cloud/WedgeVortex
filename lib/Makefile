CC = g++
CFLAGS = -O3 -shared -fPIC
TARGET = libvortex.so
SRC = vortex_core.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

clean:
	rm -f $(TARGET)
