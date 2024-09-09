# Paths
INC_DIR = include
LIB_DIR = lib
SRC_DIR = src
BIN_DIR = bin

# Compiler
CC = g++
CFLAGS = -I$(INC_DIR) -std=c++23
DEBUG_FLAGS = -g
RELEASE_FLAGS = -O2

# Source and Objects
SOURCES = $(wildcard $(SRC_DIR)/*.cpp)
DEBUG_OBJECTS = $(SOURCES:$(SRC_DIR)/%.cpp=$(BIN_DIR)/%.debug.o)
RELEASE_OBJECTS = $(SOURCES:$(SRC_DIR)/%.cpp=$(BIN_DIR)/%.release.o)

# Targets
DEBUG_TARGET = $(BIN_DIR)/toSteps-debug
RELEASE_TARGET = $(BIN_DIR)/toSteps-release

# Libraries
LIBS = -L$(LIB_DIR) -ljsoncpp

# Rules
all: release

debug: $(DEBUG_TARGET)
release: $(RELEASE_TARGET)

$(DEBUG_TARGET): $(DEBUG_OBJECTS)
	$(CC) -o $@ $^ $(LIBS)

$(RELEASE_TARGET): $(RELEASE_OBJECTS)
	$(CC) -o $@ $^ $(LIBS)

$(BIN_DIR)/%.debug.o: $(SRC_DIR)/%.cpp
	$(CC) $(CFLAGS) $(DEBUG_FLAGS) -c $< -o $@

$(BIN_DIR)/%.release.o: $(SRC_DIR)/%.cpp
	$(CC) $(CFLAGS) $(RELEASE_FLAGS) -c $< -o $@

clean:
	rm -f $(BIN_DIR)/*.o $(DEBUG_TARGET) $(RELEASE_TARGET)
