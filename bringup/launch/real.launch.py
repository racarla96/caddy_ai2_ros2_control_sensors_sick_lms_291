import yaml
from launch import LaunchDescription, LaunchContext
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command, FindExecutable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    # --- Launch arguments ---
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_rviz",
            default_value="true",
            description="Launch RViz2 for visualization."
        )
    )

    use_rviz = LaunchConfiguration("use_rviz")

    # --- Ruta del archivo de parámetros YAML ---
    lidar_params = PathJoinSubstitution([
        FindPackageShare("caddy_ai2_ros2_sensors_lidar_sick_lms_291"),
        "bringup", "config", "params.yaml"
    ])

    # Crear un contexto de lanzamiento
    context = LaunchContext()

    # Resolver la ruta real del YAML
    resolved_lidar_params_path = lidar_params.perform(context)

    # Cargar parámetros
    with open(resolved_lidar_params_path, 'r') as f:
        params = yaml.safe_load(f)

    lidar_ros_params = params["sick_lms_291_parameters"]["ros__parameters"]

    # --- Nodo del sensor SICK LMS 291 ---
    sick_node = Node(
        package="caddy_ai2_ros2_sensors_lidar_sick_lms_291",
        executable="sick_node",   # nombre del ejecutable en CMakeLists
        name="sick_lms_291_node",
        output="screen",
        parameters=[{
            'port': lidar_ros_params['port'],
            'baudrate': lidar_ros_params['baudrate'],
            'resolution': lidar_ros_params['resolution'],
            'frequency': lidar_ros_params['frequency'],
            'frame_id': lidar_ros_params['frame_id'],
        }]
    )

    # Procesar el xacro con los parámetros del YAML
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare("caddy_ai2_ros2_sensors_lidar_sick_lms_291"),
                "description", "real.urdf.xacro"]
            )
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

    # --- RViz (opcional) ---
    rviz_config_file = PathJoinSubstitution([
        FindPackageShare("caddy_ai2_ros2_sensors_lidar_sick_lms_291"),
        "description", "lidar_sick_lms_291.rviz"
    ])

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription(declared_arguments + [
        sick_node,
        node_robot_state_publisher,
        rviz_node,
    ])
