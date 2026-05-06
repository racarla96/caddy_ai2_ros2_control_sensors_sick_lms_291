import os
import yaml
from jinja2 import Environment, FileSystemLoader
from ament_index_python.packages import get_package_share_directory


def get_sensor_sdf(
    prefix='',
    parent_link='base_link',
    x=0.0, y=0.0, z=0.0,
    roll=0.0, pitch=0.0, yaw=0.0,
    with_sensor=True,
    include_parent_joint=True,
    namespace='',
    use_gpu=True,
    noise_enabled=None,
):
    """
    Render sensor.sdf.j2 and return the SDF fragment string.

    Intended for injection inside a parent robot's <model> block.
    Set include_parent_joint=True so the joint parent_link→lidar_sick_lms_291_link
    is created inside the fragment (parent_link must already exist in the model).

    noise_enabled=None reads the value from sensor_params.yaml.
    """
    pkg_share = get_package_share_directory('caddy_ai2_ros2_sensors_lidar_sick_lms_291')
    mesh_uri  = f'file://{os.path.join(pkg_share, "meshes")}/SICK_LMS291-S05.dae'

    with open(os.path.join(pkg_share, 'bringup', 'config', 'sensor_params.yaml')) as f:
        params = yaml.safe_load(f)

    if noise_enabled is None:
        noise_enabled = params.get('noise_enabled', True)

    env = Environment(
        loader=FileSystemLoader(os.path.join(pkg_share, 'description')),
        keep_trailing_newline=True,
    )

    return env.get_template('sensor.sdf.j2').render(
        prefix=prefix,
        parent_link=parent_link,
        x=x, y=y, z=z,
        roll=roll, pitch=pitch, yaw=yaw,
        mesh_uri=mesh_uri,
        include_parent_joint=include_parent_joint,
        with_sensor=with_sensor,
        namespace=namespace,
        angle_min=params['angle_min'],
        angle_max=params['angle_max'],
        range_min=params['range_min'],
        range_max=params['range_max'],
        resolution=params['resolution'],
        frequency=params['frequency'],
        use_gpu=use_gpu,
        noise_enabled=noise_enabled,
    )
