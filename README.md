# caddy_ai2_ros2_sensors_sick_lms_291

**ROS 2:** Jazzy | **Gazebo:** Harmonic | **Sensor:** SICK LMS291-S05

Driver ROS 2 + fragmento URDF inyectable para Gazebo Harmonic del LIDAR 2D SICK LMS291-S05. El driver se basa en SickToolbox (parcheado para Ubuntu 24.04). Los parámetros operativos se centralizan en `bringup/config/sensor_params.yaml` y se inyectan en tiempo de launch via Jinja2.

---

## Estructura

```
caddy_ai2_ros2_sensors_sick_lms_291/
├── bringup/
│   ├── config/
│   │   ├── sensor_params.yaml              # Parámetros operativos
│   │   └── sick_node_params.yaml.j2        # Template Jinja2 → parámetros del nodo
│   ├── launch/
│   │   ├── general.launch.py               # Launch unificado (sim + real)
│   │   └── sick_lms_291_description.py     # Helper de integración en robots padre
│   └── rviz/
│       └── lidar_sick_lms_291.rviz
├── code/src/
│   ├── sick_node.cpp                       # Nodo driver (SickToolbox)
│   └── sick_client.cpp                     # Cliente de prueba
├── description/
│   ├── sensor.urdf.j2                      # Fragmento URDF inyectable (Jinja2)
│   └── SICK_LMS291-S05.dae                 # Malla 3D
└── doc/                                    # CADs y documentación técnica
```

---

## Instalación del driver SickToolbox

```bash
cd doc/code/sicktoolbox-1.0.1-patch/
./configure
find . -type f -name Makefile -exec sed -i.bak 's/CXXFLAGS = -g -O2/CXXFLAGS = -g -O2 -std=c++11 -w/g' {} +
make && sudo make install
```

---

## Build

```bash
colcon build --packages-select caddy_ai2_ros2_sensors_sick_lms_291
source install/setup.bash
```

---

## Parámetros (`bringup/config/sensor_params.yaml`)

| Parámetro | Valor | Descripción |
|---|---|---|
| `frame_id` | `lidar_sick_lms_291_link` | Frame TF del sensor |
| `port` | `/dev/sick` | Puerto serie (alias udev RS-422) |
| `baudrate` | 500000 | bps (RS-422; máx 75 Hz) |
| `resolution` | 1.0° | Resolución angular |
| `frequency` | 75.0 Hz | Frecuencia de escaneo |
| `angle_min/max` | −90° / 90° | Rango angular |
| `range_min/max` | 0.01 / 80.0 m | Rango de distancia |

### Comunicación hardware

| Interfaz | Puerto | Baudrate | Frecuencia máx. |
|---|---|---|---|
| RS-422 → USB (activa) | `/dev/sick` | 500 000 | 75 Hz |
| RS-232 → USB | `/dev/ttyUSB0` | 38 400 | 10 Hz |

---

## Ejecución

### Hardware real

```bash
ros2 launch caddy_ai2_ros2_sensors_sick_lms_291 general.launch.py sim:=false
```

---

## Integración en un robot padre

El paquete expone el helper `sick_lms_291_description.py` con la función `get_sensor_urdf()`:

```python
from ament_index_python.packages import get_package_share_directory
import sys, os

sick_share = get_package_share_directory('caddy_ai2_ros2_sensors_sick_lms_291')
sys.path.insert(0, os.path.join(sick_share, 'bringup', 'launch'))
from sick_lms_291_description import get_sensor_urdf

fragment = get_sensor_urdf(
    prefix='',
    namespace='',
    x=0.30, y=0.0, z=0.50,
    roll=0.0, pitch=0.0, yaw=0.0,
    gazebo=True,
)
```

### Dependencia en `package.xml` del robot padre

```xml
<exec_depend>caddy_ai2_ros2_sensors_sick_lms_291</exec_depend>
```

### Bridge en el robot padre (`gz_msg_bridge.yaml.j2`)

```yaml
- ros_topic_name: "{{ ns_prefix }}sick_lms_291/scan"
  gz_topic_name:  "{{ ns_prefix }}sick_lms_291/scan"
  ros_type_name:  "sensor_msgs/msg/LaserScan"
  gz_type_name:   "gz.msgs.LaserScan"
  direction:      "GZ_TO_ROS"
  frame_id:       "{{ prefix }}lidar_sick_lms_291_link"
```

---

## Topic publicado

| Topic | Tipo | frame_id |
|---|---|---|
| `/{namespace}/sick_lms_291/scan` | `sensor_msgs/msg/LaserScan` | `{prefix}lidar_sick_lms_291_link` |

---

## Dependencias

- **ROS 2:** `rclcpp`, `sensor_msgs`, `geometry_msgs`, `tf2_ros`
- **Python (launch):** `jinja2`, `pyyaml`
- **Sistema:** SickToolbox 1.0.1 (parcheado)
- **Build:** `ament_cmake`

---

## TODOs

- [ ] Ajustar masa y momento de inercia con valores medidos
- [ ] Testear con hardware real y verificar en RViz2
- [ ] Obtener valores de ruido gaussiano del sensor real
