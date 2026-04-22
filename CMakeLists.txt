cmake_minimum_required(VERSION 3.16)
project(MemoryGame LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt5 REQUIRED COMPONENTS Widgets)

add_executable(MemoryGame
    src/main.cpp
    src/mainwindow.cpp
    src/cardwidget.cpp
    src/game.cpp
    src/scoremanager.cpp
)

target_link_libraries(MemoryGame Qt5::Widgets)

# Icon dosyası (opsiyonel)
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/mymem.png")
    file(COPY mymem.png DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
endif()
