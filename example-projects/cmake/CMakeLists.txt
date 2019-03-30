cmake_minimum_required(VERSION 3.0)

project("appimagecraft example project")

add_executable(example main.c)

install(TARGETS example RUNTIME DESTINATION bin)
