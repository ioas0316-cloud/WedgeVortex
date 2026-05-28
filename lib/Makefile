CC = g++
CFLAGS = -O3 -shared -fPIC
TARGET = libvortex.so
SRC = ../src/phase_kernel.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

clean:
	rm -f $(TARGET)
