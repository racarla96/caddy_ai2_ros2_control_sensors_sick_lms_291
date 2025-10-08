import trimesh
import numpy as np

mesh = trimesh.load("../meshes/SICK_LMS291-S05.stl")
mass = 4.5  # kg

# Bounding box
bbox = mesh.bounding_box.extents
bbox_center = mesh.bounding_box.centroid

# Inercia y centro de masa
center_of_mass = mesh.center_mass
inertia_matrix = mesh.moment_inertia * (mass / mesh.volume)

# Formato URDF
urdf_snippet = f"""
<link name="lidar_sick_lms_291_link">
  <visual>
    <geometry>
      <mesh filename="package://mi_paquete/meshes/SICK_LMS291-S05.stl"/>
    </geometry>
    <origin xyz="0 0 0" rpy="0 0 0"/>
  </visual>

  <collision>
    <geometry>
      <box>
        <size>{bbox[0]:.3f} {bbox[1]:.3f} {bbox[2]:.3f}</size>
      </box>
    </geometry>
    <origin xyz="{bbox_center[0]:.3f} {bbox_center[1]:.3f} {bbox_center[2]:.3f}" rpy="0 0 0"/>
  </collision>

  <inertial>
    <mass value="{mass:.3f}"/>
    <origin xyz="{center_of_mass[0]:.3f} {center_of_mass[1]:.3f} {center_of_mass[2]:.3f}" rpy="0 0 0"/>
    <inertia ixx="{inertia_matrix[0,0]:.6f}" ixy="{inertia_matrix[0,1]:.6f}" ixz="{inertia_matrix[0,2]:.6f}"
             iyy="{inertia_matrix[1,1]:.6f}" iyz="{inertia_matrix[1,2]:.6f}" izz="{inertia_matrix[2,2]:.6f}"/>
  </inertial>
</link>
"""

print(urdf_snippet)
