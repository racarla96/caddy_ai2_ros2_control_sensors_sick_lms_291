from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # Arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "gui",
            default_value="true",
            description="Launch Gazebo with GUI (true) or headless (false).",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "prefix",
            default_value="",
            description="Prefix for the robot links and joints.",
        )
    )

    gui = LaunchConfiguration("gui")
    prefix = LaunchConfiguration("prefix")

    # Gazebo GUI / headless
    gazebo = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
    [FindPackageShare("ros_gz_sim"), "/launch/gz_sim.launch.py"]
    ),
    launch_arguments=[("gz_args", " -r -v 3 empty.sdf")],
    condition=IfCondition(gui),
    )

    gazebo_headless = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
    [FindPackageShare("ros_gz_sim"), "/launch/gz_sim.launch.py"]
    ),
    launch_arguments=[("gz_args", ["--headless-rendering -s -r -v 3 empty.sdf"])],
    condition=UnlessCondition(gui),
    )

    # Gazebo ↔ ROS 2 bridge
    gazebo_bridge = Node(
    package="ros_gz_bridge",
    executable="parameter_bridge",
    arguments=[
    "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
    "/sick_lms_291/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
    ],
    output="screen",
    )

    # Procesar el xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare("caddy_ai2_ros2_control_sensors_lidar_sick_lms_291"),
                "description", "urdf", "lidar_sick_lms_291_sim.urdf.xacro"]
            ),
            " ",
            "use_sim_gazebo:=true",
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    # Publicar el URDF
    node_robot_state_publisher = Node(
    package="robot_state_publisher",
    executable="robot_state_publisher",
    output="screen",
    parameters=[robot_description],
    )

    # Spawnear en Gazebo
    gz_spawn_entity = Node(
    package="ros_gz_sim",
    executable="create",
    output="screen",
    arguments=[
    "-topic", "/robot_description",
    "-name", "lidar_sick_lms_291",
    "-allow_renaming", "true",
    ],
    )

    # Cargar parámetros del YAML para el nodo del sensor
    config_file = PathJoinSubstitution(
        [FindPackageShare("caddy_ai2_ros2_control_sensors_lidar_sick_lms_291"),
        "config", "lidar_sick_lms_291.yaml"]
    )
    
    # Nodo del driver del sensor (para hardware real)
    sick_lms_291_node = Node(
        package="sick_lms_291_driver",  # Ajustar según el paquete real
        executable="sick_lms_291_node",
        name="sick_lms_291_node",
        parameters=[config_file],
        output="screen",
        condition=UnlessCondition(gui),  # Solo en modo headless/real
    )

    # Lanzar RViz (opcional)
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("caddy_ai2_ros2_control_sensors_lidar_sick_lms_291"),
        "tools", "rviz", "lidar_sick_lms_291.rviz"]
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        condition=IfCondition(gui),
    )

    nodes = [
        gazebo,
        gazebo_headless,
        gazebo_bridge,
        node_robot_state_publisher,
        gz_spawn_entity,
        sick_lms_291_node,
        rviz_node,
    ]

    return LaunchDescription(declared_arguments + nodes)