from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import os

from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_share = get_package_share_directory('caddy_ai2_ros2_control_sensors_SICK_LMS291')

    urdf_file = os.path.join(pkg_share, 'urdf', 'sick_lms_291.urdf.xacro')

    return LaunchDescription([

        DeclareLaunchArgument(
            'rvizconfig',
            default_value=os.path.join(pkg_share, 'rviz', 'sick_lms_291.rviz'),
            description='Archivo RViz config'
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[{'use_sim_time': False}],
            arguments=[urdf_file]
        ),

        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui'
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', LaunchConfiguration('rvizconfig')]
        )
    ])
