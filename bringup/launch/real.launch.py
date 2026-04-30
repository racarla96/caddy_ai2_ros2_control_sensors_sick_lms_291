import os
import sys
import tempfile

import yaml
from jinja2 import Environment, FileSystemLoader
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_rviz',    default_value='true',
                              description='Launch RViz2 for visualization.'),
        DeclareLaunchArgument('prefix',      default_value='',
                              description='Name prefix for all links and joints.'),
        DeclareLaunchArgument('namespace',   default_value='',
                              description='ROS 2 namespace for the scan topic.'),
        DeclareLaunchArgument('parent_link', default_value='world',
                              description='Parent link the sensor joint attaches to.'),
        DeclareLaunchArgument('x',     default_value='0.0', description='X offset from parent_link (m).'),
        DeclareLaunchArgument('y',     default_value='0.0', description='Y offset from parent_link (m).'),
        DeclareLaunchArgument('z',     default_value='0.0', description='Z offset from parent_link (m).'),
        DeclareLaunchArgument('roll',  default_value='0.0', description='Roll from parent_link (rad).'),
        DeclareLaunchArgument('pitch', default_value='0.0', description='Pitch from parent_link (rad).'),
        DeclareLaunchArgument('yaw',   default_value='0.0', description='Yaw from parent_link (rad).'),
        OpaqueFunction(function=_launch),
    ])


def _launch(context, *args, **kwargs):
    lc = context.launch_configurations

    use_rviz    = lc['use_rviz'].lower() == 'true'
    prefix      = lc['prefix']
    namespace   = lc['namespace']
    parent_link = lc['parent_link']
    x           = float(lc['x'])
    y           = float(lc['y'])
    z           = float(lc['z'])
    roll        = float(lc['roll'])
    pitch       = float(lc['pitch'])
    yaw         = float(lc['yaw'])

    pkg_share = get_package_share_directory('caddy_ai2_ros2_sensors_lidar_sick_lms_291')
    mesh_dir  = os.path.join(pkg_share, 'meshes')

    with open(os.path.join(pkg_share, 'bringup', 'config', 'sensor_params.yaml')) as f:
        sensor = yaml.safe_load(f)

    hw = sensor['hardware']
    op = sensor['operation']
    si = sensor['simulation']
    no = si['noise']

    cfg_env = Environment(
        loader=FileSystemLoader(os.path.join(pkg_share, 'bringup', 'config')),
        keep_trailing_newline=True,
    )
    node_params_str = cfg_env.get_template('sick_node_params.yaml.j2').render(**sensor)

    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.yaml', prefix='sick_params_', delete=False
    )
    tmp.write(node_params_str)
    tmp.close()

    desc_env = Environment(
        loader=FileSystemLoader(os.path.join(pkg_share, 'description')),
        keep_trailing_newline=True,
    )

    robot_description_str = desc_env.get_template('standalone.sdf.j2').render(
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
        use_gpu=False,
        mesh_uri=f'file://{mesh_dir}/SICK_LMS291-S05.dae',
        noise_enabled=False,
        noise_type=no['type'],
        noise_mean=no['mean'],
        noise_stddev=no['stddev'],
        noise_bias_mean=no['bias_mean'],
        noise_bias_stddev=no['bias_stddev'],
        include_plugin=False,
    )

    nodes = [
        Node(
            package='caddy_ai2_ros2_sensors_lidar_sick_lms_291',
            executable='sick_node',
            name='sick_lms_291_node',
            output='screen',
            parameters=[tmp.name],
            namespace=namespace,
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description_str}],
        ),
    ]

    if use_rviz:
        rviz_cfg = os.path.join(pkg_share, 'bringup', 'rviz', 'lidar_sick_lms_291.rviz')
        nodes.append(Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='log',
            arguments=['-d', rviz_cfg],
        ))

    return nodes
