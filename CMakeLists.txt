cmake_minimum_required(VERSION 3.5)
project(caddy_ai2_ros2_sensors_lidar_sick_lms_291)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rmw REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

# Incluye los directorios de encabezados de la biblioteca externa
include_directories(/usr/local/include/sicklms-1.0)

# Encuentra la biblioteca externa
find_library(SICKLMS_LIB NAMES sicklms-1.0 PATHS /usr/local/lib)

# Asegúrate de que la biblioteca se encontró
if(NOT SICKLMS_LIB)
  message(FATAL_ERROR "sicklms library not found")
endif()

include_directories(
  ${PROJECT_SOURCE_DIR}/code/src
)

add_executable(sick_node code/src/sick_node.cpp)
ament_target_dependencies(sick_node
  "rclcpp"
  "sensor_msgs"
  "visualization_msgs"
  "geometry_msgs"
)
target_link_libraries(sick_node ${SICKLMS_LIB})

add_executable(sick_client code/src/sick_client.cpp)
ament_target_dependencies(sick_client
  "rclcpp"
  "sensor_msgs"
  "visualization_msgs"
  "geometry_msgs"
)

install(TARGETS
  sick_node sick_client
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY bringup description
  DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
