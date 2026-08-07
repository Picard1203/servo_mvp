# Host-native tests for the sketch's pure-logic classes.
# No Arduino, no board, no extra libraries - just a C++ compiler.
#
#   make        build and run
#   make clean

CXX      ?= g++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -Wpedantic -Werror -O1
BINARY   := run_tests

.PHONY: all clean
all: $(BINARY)
	./$(BINARY)

$(BINARY): test_pure_logic.cpp TinyTest.h \
           ../../src/AngleMath.h ../../src/ServoStatus.h \
           ../../src/SignMagnitude.h ../../src/ServoRegisters.h
	$(CXX) $(CXXFLAGS) -o $@ test_pure_logic.cpp

clean:
	rm -f $(BINARY)
