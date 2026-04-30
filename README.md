# SICK LMS291-S05 ROS 2 Driver

## TODOs
- [x] Fuente de verdad única: `bringup/config/sensor_params.yaml` leído por launch files y plantillas Jinja2.
- [x] Descripción migrada de xacro a Jinja2 + SDF 1.11 nativo (Gazebo Harmonic).
- [x] Fragmentos inyectables (`sensor.sdf.j2`, `plugin.sdf.j2`) para integración en simulaciones externas.
- [x] Soporte de `prefix`, `namespace` y `parent_link` en todos los launch files.
- [x] Revisar y adecuar la documentación.
- [ ] Calcular la altura del haz respecto a su base para ajustar el offset de montaje.
- [ ] Ajustar la masa y el momento de inercia con valores medidos.
- [ ] Testear con el hardware real y visualizar en RViz2.
- [ ] Obtener los valores de ruido gaussiano para la simulación → https://sdformat.org/spec?ver=1.11&elem=sensor#sensor_lidar

NOTA: De momento, no hay soporte para LIDARs en el paquete ROS2 Control.

---

Este repositorio contiene el código fuente, documentación, CADs y drivers para integrar el sensor **SICK LMS291-S05** en un entorno **ROS 2 Jazzy + Gazebo Harmonic**. El driver está basado en **SickToolbox** y adaptado para versiones modernas de Linux y ROS 2. Los parámetros físicos y operativos se centralizan en `bringup/config/sensor_params.yaml`, del que se generan automáticamente la descripción del robot y los parámetros del nodo mediante **Jinja2**.

El paquete está diseñado para ser **inyectable** en la simulación de un robot padre: expone dos fragmentos SDF (`sensor.sdf.j2` y `plugin.sdf.j2`) que el robot padre incluye en su propio modelo mediante `IncludeLaunchDescription`.

---

## Estructura del Repositorio

```
caddy_ai2_ros2_sensors_sick_lms_291/
├── CMakeLists.txt
├── package.xml
├── README.md
├── code/src/
│   ├── sick_node.cpp            # Nodo principal del driver (SickToolbox)
│   └── sick_client.cpp          # Subscriber de prueba
├── bringup/
│   ├── config/
│   │   ├── sensor_params.yaml        # Fuente de verdad única (hardware + operación + simulación)
│   │   └── sick_node_params.yaml.j2  # Plantilla Jinja2 → parámetros ROS 2 del nodo
│   ├── launch/
│   │   ├── real.launch.py       # Hardware real: sick_node + RSP + RViz2
│   │   └── sim.launch.py        # Simulación standalone: Gazebo + bridge + RSP + RViz2
│   └── rviz/
│       └── lidar_sick_lms_291.rviz
├── description/
│   ├── sensor.sdf.j2            # Fragmento inyectable: joint + links + sensor (gpu/cpu)
│   ├── plugin.sdf.j2            # Fragmento inyectable <model>: gz-sim-sensors-system
│   ├── gui_plugin.sdf.j2        # Fragmento inyectable <gui>: VisualizeLidar
│   ├── standalone.sdf.j2        # Modelo SDF autocontenido (para RSP y spawn externo)
│   └── standalone_world.sdf.j2  # Mundo Gazebo completo para test autónomo
├── meshes/
│   ├── SICK_LMS291-S05.dae
│   └── SICK_LMS291-S05.stl
└── doc/
    ├── cad/                     # Modelos 3D del sensor (STP, IGS, SLDASM, PLY)
    └── ...                      # Manuales técnicos y documentación oficial
```

---

## Instalación del Driver SickToolbox

El sensor utiliza **SickToolbox** como backend de comunicación. Se incluye una versión **parchada para Ubuntu 24.04 LTS**.

```bash
cd doc/code/sicktoolbox-1.0.1-patch/
./configure
find . -type f -name Makefile -exec sed -i.bak 's/CXXFLAGS = -g -O2/CXXFLAGS = -g -O2 -std=c++11 -w/g' {} +
make
sudo make install
```

---

## Compilación

```bash
cd <workspace>
colcon build --packages-select caddy_ai2_ros2_sensors_lidar_sick_lms_291
source install/setup.bash
```

---

## Ejecución

### Hardware real

```bash
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 real.launch.py
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 real.launch.py use_rviz:=false

# Con pose de montaje explícita
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 real.launch.py \
    parent_link:=base_link x:=0.3 z:=0.5 yaw:=0.0
```

Publica `/sick_lms_291/scan` (`sensor_msgs/LaserScan`) y difunde las TF del sensor vía `robot_state_publisher`.

### Simulación standalone (Gazebo)

```bash
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 sim.launch.py
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 sim.launch.py gui:=false

# Forzar ruido activo/desactivo independientemente del YAML
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 sim.launch.py noise:=true
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 sim.launch.py noise:=false

# Con prefix, namespace y pose
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 sim.launch.py \
    prefix:=front_  namespace:=robot1  z:=0.5  use_gpu:=true
```

El flag `noise` tiene tres estados: vacío → lee `sensor_params.yaml`; `true`/`false` → sobreescribe el YAML.

---

## Comunicación con el Sensor

| Interfaz | Puerto | Baudrate | Frecuencia máx. | Resolución mín. |
|----------|--------|----------|-----------------|-----------------|
| RS-422 → USB *(activa)* | `/dev/sick` | 500 000 | **75 Hz** | 0.25° |
| RS-232 → USB | `/dev/ttyUSB0` | 38 400 | 10 Hz | 0.5° |

---

## Arquitectura

```
bringup/config/sensor_params.yaml
        │
        ├─[Jinja2]──► sick_node_params.yaml.j2 ──► sick_node (real)
        │
        └─[Jinja2]──► description/standalone.sdf.j2
                              │
                              ├── {% include 'sensor.sdf.j2' %}   ← joint + links + sensor
                              └── {% include 'plugin.sdf.j2' %}   ← gz-sim-sensors-system

sim.launch.py:  standalone_world.sdf.j2 ──► Gazebo (mundo completo, sensor embebido)
                standalone.sdf.j2       ──► robot_state_publisher (TF + RViz)

real.launch.py: standalone.sdf.j2 (include_plugin=False) ──► robot_state_publisher
```

---

## Parámetros — `bringup/config/sensor_params.yaml`

Fichero YAML con tres secciones. Es la **única fuente de verdad**: los launch files lo leen y renderizan las plantillas Jinja2. La pose de montaje (`x, y, z, roll, pitch, yaw`) y el `parent_link` son **siempre externos** — se pasan como argumentos del launch.

```yaml
hardware:
  weight: 4.5               # kg
  frame_id: "laser_frame"   # TF frame del driver y origen del haz en simulación

operation:
  port: "/dev/sick"         # Puerto serie (alias udev)
  baudrate: 500000          # bps; debe coincidir con los jumpers hardware
  resolution: 1.0           # deg; opciones: 0.25, 0.5, 1.0
  frequency: 75.0           # Hz; máx 75 en RS-422

simulation:
  angle_min: -90.0          # deg
  angle_max:  90.0          # deg
  range_min:  0.01          # m
  range_max:  80.0          # m
  noise:
    enabled: true           # Sobreescribible con noise:= en el launch
    type: "gaussian"
    mean: 0.0               # m
    stddev: 0.01            # m (típico LiDAR: 0.005–0.02)
    bias_mean: 0.0
    bias_stddev: 0.0
```

### Mensaje `/sick_lms_291/scan`

- Tipo: `sensor_msgs/msg/LaserScan`
- `angle_min = -1.5708 rad` / `angle_max = 1.5708 rad`
- `angle_increment = resolution (rad)`
- `ranges[]` en metros
- `scan_time = 1 / frequency`

---

## Fragmentos SDF — `description/`

| Fichero | Contenido | Uso |
|---------|-----------|-----|
| `sensor.sdf.j2` | `{{ prefix }}lidar_joint` + links + sensor gpu/cpu | Inyectar en `<model>` del robot padre |
| `plugin.sdf.j2` | `gz-sim-sensors-system` a nivel `<model>` | Inyectar en `<model>` del robot si no lo tiene |
| `gui_plugin.sdf.j2` | `VisualizeLidar` | Inyectar en `<gui>` del mundo del robot |
| `standalone.sdf.j2` | Modelo autocontenido (sin plugin de mundo) | `robot_state_publisher` (TF + RViz) |
| `standalone_world.sdf.j2` | Mundo completo: sensor + sensors-system + GUI | `sim.launch.py` (Gazebo standalone) |

Variables requeridas por `sensor.sdf.j2`:

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `prefix` | str | Prefijo de nombres (puede ser `''`) |
| `namespace` | str | Namespace ROS 2 del topic (puede ser `''`) |
| `parent_link` | str | Link padre en el modelo |
| `x, y, z` | float | Traslación desde `parent_link` (m) |
| `roll, pitch, yaw` | float | Rotación desde `parent_link` (rad) |
| `frame_id` | str | Nombre del link origen del haz |
| `weight` | float | Masa del sensor (kg) |
| `angle_min/max` | float | Ángulos de barrido (deg) |
| `range_min/max` | float | Límites de rango (m) |
| `frequency` | float | Tasa de actualización (Hz) |
| `resolution` | float | Resolución angular (deg) |
| `use_gpu` | bool | `gpu_lidar` si True, `lidar` (cpu) si False |
| `mesh_uri` | str | URI `file://` de la malla DAE |
| `noise_enabled` | bool | Activar ruido gaussiano |
| `noise_type/mean/stddev/bias_mean/bias_stddev` | — | Parámetros del modelo de ruido |

`standalone.sdf.j2` admite además `include_plugin` (bool, por defecto `true`) para suprimir el fragmento de plugin cuando no se necesita Gazebo (ej. `real.launch.py`).

---

## Integración en la Simulación de un Robot Padre

El robot padre incluye este sensor vía `IncludeLaunchDescription`, pasando `prefix`, `namespace`, `parent_link` y la pose de montaje como argumentos:

```python
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

sick_share = get_package_share_directory('caddy_ai2_ros2_sensors_lidar_sick_lms_291')

IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        os.path.join(sick_share, 'bringup', 'launch', 'sim.launch.py')
    ),
    launch_arguments={
        'prefix':      'front_',
        'namespace':   'robot1',
        'parent_link': 'base_link',
        'x':    '0.30',
        'z':    '0.50',
        'yaw':  '0.0',
        'use_gpu': 'true',
        'gui':  'false',
    }.items(),
)
```

Para inyectar solo los fragmentos SDF en el modelo del robot (sin lanzar Gazebo desde aquí), el robot padre lee y renderiza los fragmentos directamente:

```python
import yaml
from jinja2 import Environment, FileSystemLoader
from ament_index_python.packages import get_package_share_directory

sick_share = get_package_share_directory('caddy_ai2_ros2_sensors_lidar_sick_lms_291')

with open(os.path.join(sick_share, 'bringup', 'config', 'sensor_params.yaml')) as f:
    sensor = yaml.safe_load(f)

env = Environment(loader=FileSystemLoader(os.path.join(sick_share, 'description')))

sensor_fragment = env.get_template('sensor.sdf.j2').render(
    prefix='front_',
    namespace='robot1',
    parent_link='base_link',
    x=0.30, y=0.0, z=0.50,
    roll=0.0, pitch=0.0, yaw=0.0,
    frame_id=sensor['hardware']['frame_id'],
    weight=sensor['hardware']['weight'],
    angle_min=sensor['simulation']['angle_min'],
    angle_max=sensor['simulation']['angle_max'],
    range_min=sensor['simulation']['range_min'],
    range_max=sensor['simulation']['range_max'],
    frequency=sensor['operation']['frequency'],
    resolution=sensor['operation']['resolution'],
    use_gpu=True,
    mesh_uri=f'file://{os.path.join(sick_share, "meshes")}/SICK_LMS291-S05.dae',
    noise_enabled=sensor['simulation']['noise']['enabled'],
    noise_type=sensor['simulation']['noise']['type'],
    noise_mean=sensor['simulation']['noise']['mean'],
    noise_stddev=sensor['simulation']['noise']['stddev'],
    noise_bias_mean=sensor['simulation']['noise']['bias_mean'],
    noise_bias_stddev=sensor['simulation']['noise']['bias_stddev'],
)
```

### Topic bridge en el robot padre

```yaml
# gz_msg_bridge.yaml.j2 del paquete host
- ros_topic_name: "{{ ns }}sick_lms_291/scan"
  gz_topic_name:  "{{ ns }}sick_lms_291/scan"
  ros_type_name:  "sensor_msgs/msg/LaserScan"
  gz_type_name:   "gz.msgs.LaserScan"
  direction:      GZ_TO_ROS
```

### Nota sobre el mesh URI

El patrón `package://` no funciona cuando Gazebo carga el SDF directamente. Gazebo solo resuelve `package://` cuando recibe el modelo a través del topic `/robot_description`. Para garantizar que el mesh se carga en ambos modos, el URI se inyecta como ruta absoluta `file://` desde Python antes de que el SDF llegue a Gazebo.

---

## Dependencias

- **ROS 2 Jazzy:** `rclcpp`, `sensor_msgs`, `geometry_msgs`, `visualization_msgs`, `tf2_ros`, `ros_gz_sim`, `ros_gz_bridge`, `robot_state_publisher`
- **Python (launch):** `jinja2`, `pyyaml`
- **Sistema:** `sicktoolbox-1.0.1-patch`, compilador C++14+
- **Construcción:** `ament_cmake`

---

## Recursos Útiles

- [REP 103 — Unidades y convenciones ROS](https://www.ros.org/reps/rep-0103.html)
- [SDFormat 1.11 — sensor/lidar](https://sdformat.org/spec?ver=1.11&elem=sensor#sensor_lidar)
- SickToolbox Quickstart: `doc/code/sicktoolbox-quickstart.pdf`
