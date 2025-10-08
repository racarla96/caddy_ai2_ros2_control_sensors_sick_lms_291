import yaml
from launch import LaunchDescription, LaunchContext
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


    # Ruta del YAML
    lidar_params = PathJoinSubstitution(
        [FindPackageShare("caddy_ai2_ros2_sensors_lidar_sick_lms_291"),
        "bringup", "config", "params.yaml"]
    )

    # Crear un contexto de lanzamiento
    context = LaunchContext()

    # Resolver el valor real de la Substitution
    resolved_lidar_params_path = lidar_params.perform(context)

    # Cargar parámetros del YAML
    with open(resolved_lidar_params_path, 'r') as f:
        params = yaml.safe_load(f)

    lidar_ros_params = params["sick_lms_291_parameters"]["ros__parameters"]

    # Suponiendo que en YAML está en grados y resolución en grados
    samples = int((lidar_ros_params["angle_max"] - lidar_ros_params["angle_min"]) / lidar_ros_params["resolution"] )
    angle_min_rad = lidar_ros_params["angle_min"] * 3.1416 / 180.0
    angle_max_rad = lidar_ros_params["angle_max"] * 3.1416 / 180.0

    # Procesar el xacro con los parámetros del YAML
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare("caddy_ai2_ros2_sensors_lidar_sick_lms_291"),
                "description", "sim.urdf.xacro"]
            ),
            " ",
            f"samples:={samples} ",
            f"angle_min:={angle_min_rad} ",
            f"angle_max:={angle_max_rad} ",
            f"frequency:={lidar_ros_params['frequency']} ",
            f"range_min:={lidar_ros_params['min_range']} ",
            f"range_max:={lidar_ros_params['max_range']} ",
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    # Robot State Publisher
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

    # Lanzar RViz (opcional)
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("caddy_ai2_ros2_sensors_lidar_sick_lms_291"),
        "description", "lidar_sick_lms_291.rviz"]
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
        rviz_node,
    ]

    return LaunchDescription(declared_arguments + nodes)