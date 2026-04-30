import os
import tempfile

import yaml
from jinja2 import Environment, FileSystemLoader
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('gui',         default_value='true',
                              description='Launch Gazebo with GUI (true) or headless (false).'),
        DeclareLaunchArgument('noise',       default_value='',
                              description='Enable noise: true|false. Empty reads sensor_params.yaml.'),
        DeclareLaunchArgument('use_gpu',     default_value='true',
                              description='Use gpu_lidar (true) or cpu lidar (false).'),
        DeclareLaunchArgument('prefix',      default_value='',
                              description='Name prefix for all links and joints.'),
        DeclareLaunchArgument('namespace',   default_value='',
                              description='ROS 2 namespace for the scan topic.'),
        DeclareLaunchArgument('parent_link', default_value='world',
                              description='Parent link the sensor joint attaches to (injection only).'),
        DeclareLaunchArgument('x',     default_value='0.0', description='X offset (m).'),
        DeclareLaunchArgument('y',     default_value='0.0', description='Y offset (m).'),
        DeclareLaunchArgument('z',     default_value='0.0', description='Z offset (m).'),
        DeclareLaunchArgument('roll',  default_value='0.0', description='Roll (rad).'),
        DeclareLaunchArgument('pitch', default_value='0.0', description='Pitch (rad).'),
        DeclareLaunchArgument('yaw',   default_value='0.0', description='Yaw (rad).'),
        OpaqueFunction(function=_launch),
    ])


def _launch(context, *args, **kwargs):
    lc = context.launch_configurations

    gui         = lc['gui'].lower() == 'true'
    noise_arg   = lc['noise']
    use_gpu     = lc['use_gpu'].lower() == 'true'
    prefix      = lc['prefix']
    namespace   = lc['namespace']
    parent_link = lc['parent_link']
    x           = float(lc['x'])
    y           = float(lc['y'])
    z           = float(lc['z'])
    roll        = float(lc['roll'])
    pitch       = float(lc['pitch'])
    yaw         = float(lc['yaw'])

    pkg_share    = get_package_share_directory('caddy_ai2_ros2_sensors_lidar_sick_lms_291')
    gz_sim_share = get_package_share_directory('ros_gz_sim')
    mesh_dir     = os.path.join(pkg_share, 'meshes')

    with open(os.path.join(pkg_share, 'bringup', 'config', 'sensor_params.yaml')) as f:
        sensor = yaml.safe_load(f)

    hw = sensor['hardware']
    op = sensor['operation']
    si = sensor['simulation']
    no = si['noise']

    noise_enabled = no['enabled'] if noise_arg == '' else noise_arg.lower() == 'true'

    desc_env = Environment(
        loader=FileSystemLoader(os.path.join(pkg_share, 'description')),
        keep_trailing_newline=True,
    )

    render_params = dict(
        prefix=prefix,
        namespace=namespace,
        parent_link=parent_link,
        x=x, y=y, z=z,
        roll=roll, pitch=pitch, yaw=yaw,
        frame_id=hw['frame_id'],
        weight=hw['weight'],
        angle_min=si['angle_min'],
        angle_max=si['angle_max'],
        range_min=si['range_min'],
        range_max=si['range_max'],
        frequency=op['frequency'],
        resolution=op['resolution'],
        use_gpu=use_gpu,
        mesh_uri=f'file://{mesh_dir}/SICK_LMS291-S05.dae',
        noise_enabled=noise_enabled,
        noise_type=no['type'],
        noise_mean=no['mean'],
        noise_stddev=no['stddev'],
        noise_bias_mean=no['bias_mean'],
        noise_bias_stddev=no['bias_stddev'],
    )

    # World SDF: sensor embedded, gz-sim-sensors-system at world level, GUI plugins
    world_str = desc_env.get_template('standalone_world.sdf.j2').render(
        **render_params, gui=gui
    )
    tmp_world = tempfile.NamedTemporaryFile(
        mode='w', suffix='.sdf', prefix='sick_world_', delete=False
    )
    tmp_world.write(world_str)
    tmp_world.close()

    # RSP uses standalone.sdf.j2 (model-only, no world/GUI elements)
    sdf_str = desc_env.get_template('standalone.sdf.j2').render(
        **render_params, include_plugin=False
    )

    scan_topic = f'/{namespace}/sick_lms_291/scan' if namespace else '/sick_lms_291/scan'
    gz_args = f'--headless-rendering -s -r {tmp_world.name} -v 3' if not gui \
              else f'-r {tmp_world.name} -v 3'

    nodes = [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(gz_sim_share, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments=[('gz_args', gz_args)],
        ),
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                f'{scan_topic}@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            ],
            output='screen',
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': sdf_str, 'use_sim_time': True}],
        ),
    ]

    if gui:
        rviz_cfg = os.path.join(pkg_share, 'bringup', 'rviz', 'lidar_sick_lms_291.rviz')
        nodes.append(Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='log',
            arguments=['-d', rviz_cfg],
        ))

    return nodes
