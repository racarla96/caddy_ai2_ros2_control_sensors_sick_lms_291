# SICK LMS291-S05 ROS 2 Driver

## TODOs
- [ ] Ajustar la masa y el momento de inercia con valores medidos.
- [ ] Testear con el hardware real y visualizar en RViz2.
- [ ] Obtener los valores de ruido gaussiano para la simulación → https://sdformat.org/spec?ver=1.11&elem=sensor#sensor_lidar

NOTA: De momento, no hay soporte para LIDARs en el paquete ROS2 Control.

---

Este repositorio contiene el código fuente, documentación, CADs y drivers para integrar el sensor **SICK LMS291-S05** en un entorno **ROS 2 Jazzy + Gazebo Harmonic**. El driver está basado en **SickToolbox** y adaptado para versiones modernas de Linux y ROS 2.

Los parámetros operativos se centralizan en `bringup/config/sensor_params.yaml`. Las constantes físicas del sensor (masa, inercia, frame_id, modelo de ruido) van hardcodeadas en las plantillas SDF. La descripción del robot y los parámetros del nodo se generan automáticamente mediante **Jinja2**.

El paquete está diseñado para ser **inyectable** en el modelo de un robot padre: `sensor.sdf.j2` se incluye dentro del bloque `<model>` del robot padre. Para uso standalone, `world.sdf.j2` genera el mundo Gazebo completo (con sensor horneado) y el modelo para `robot_state_publisher`.

El origen del link `lidar_sick_lms_291_link` está en la **apertura óptica** del sensor. Visual, colisión e inercia tienen un offset de −0.025 m en Z para alinearse con el cuerpo físico.

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
│   │   ├── sensor_params.yaml        # Parámetros operativos (8 claves planas)
│   │   └── sick_node_params.yaml.j2  # Plantilla Jinja2 → parámetros ROS 2 del nodo
│   ├── launch/
│   │   └── general.launch.py    # Launch unificado: sim + real, con todos los parámetros
│   └── rviz/
│       └── lidar_sick_lms_291.rviz
├── description/
│   ├── sensor.sdf.j2            # Fragmento inyectable: link + joint [+ sensor Gazebo]
│   └── world.sdf.j2             # Mundo Gazebo completo o modelo standalone para RSP
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

El paquete tiene un único launch: `general.launch.py`.

### Simulación (Gazebo con GUI)

```bash
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 general.launch.py sim:=true

# Sin RViz2
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 general.launch.py sim:=true rviz:=false

# Forzar ruido activo/desactivo
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 general.launch.py sim:=true use_noise:=true
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 general.launch.py sim:=true use_noise:=false

# Con prefix, namespace y pose de montaje
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 general.launch.py \
    sim:=true prefix:=front_ namespace:=robot1 z:=0.5 use_gpu:=true
```

### Hardware real

```bash
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 general.launch.py sim:=false

# Sin RViz2, con pose de montaje explícita
ros2 launch caddy_ai2_ros2_sensors_lidar_sick_lms_291 general.launch.py \
    sim:=false rviz:=false parent_link:=base_link x:=0.3 z:=0.5
```

Publica `/{namespace}/sick_lms_291/scan` (`sensor_msgs/LaserScan`) con `frame_id = lidar_sick_lms_291_link`.

### Parámetros del launch

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `sim` | `true` | `true` → Gazebo + bridge; `false` → hardware real |
| `rviz` | `true` | Lanza RViz2 |
| `use_noise` | `''` | Vacío → lee yaml; `true`/`false` → sobreescribe |
| `use_gpu` | `true` | `gpu_lidar` (true) o `lidar` cpu (false). Solo sim. |
| `prefix` | `''` | Prefijo de nombres de links y joints |
| `namespace` | `''` | Namespace ROS 2 del topic de scan |
| `parent_link` | `map` | Frame padre para el TF del sensor |
| `x y z` | `0.0` | Traslación (m) |
| `roll pitch yaw` | `0.0` | Rotación (rad) |

---

## Comunicación con el Sensor

| Interfaz | Puerto | Baudrate | Frecuencia máx. | Resolución mín. |
|----------|--------|----------|-----------------|-----------------|
| RS-422 → USB *(activa)* | `/dev/sick` | 500 000 | **75 Hz** | 0.25° |
| RS-232 → USB | `/dev/ttyUSB0` | 38 400 | 10 Hz | 0.5° |

---

## Arquitectura

```
bringup/config/sensor_params.yaml   (8 claves planas)
        │
        ├─[Jinja2]──► sick_node_params.yaml.j2 ──► sick_node (sim:=false)
        │
        └─[Jinja2]──► description/world.sdf.j2
                            │
                            ├─ model_only=false ──► mundo Gazebo completo (sensor horneado)
                            └─ model_only=true
                                  ├─ with_sensor=false ──► robot_description para RSP
                                  └─ with_sensor=true  ──► modelo standalone con sensor

general.launch.py (sim:=true):
  world.sdf.j2 (model_only=false, gui=true)       ──► Gazebo (sensor en mundo)
  world.sdf.j2 (model_only=true, with_sensor=false) ──► robot_state_publisher (TF)

general.launch.py (sim:=false):
  sick_node_params.yaml.j2  ──► sick_node
  world.sdf.j2 (model_only=true, with_sensor=false) ──► robot_state_publisher (TF)
```

### TF tree (standalone)

```
map
 └─[lidar_joint]─► lidar_sick_lms_291_link   (origen = apertura óptica)
```

---

## Parámetros — `bringup/config/sensor_params.yaml`

```yaml
port:       "/dev/sick"   # Puerto serie (alias udev para el adaptador RS-422)
baudrate:   500000        # bps; debe coincidir con los jumpers hardware
resolution: 1.0           # deg; opciones: 0.25, 0.5, 1.0
frequency:  75.0          # Hz; máx 75 en RS-422
angle_min: -90.0          # deg
angle_max:  90.0          # deg
range_min:  0.01          # m
range_max:  80.0          # m
```

### Mensaje de scan

- Tipo: `sensor_msgs/msg/LaserScan`
- `frame_id = lidar_sick_lms_291_link`
- `angle_min = -1.5708 rad` / `angle_max = 1.5708 rad`
- `angle_increment = resolution (rad)`
- `scan_time = 1 / frequency`

---

## Plantillas SDF — `description/`

### `sensor.sdf.j2` — fragmento inyectable en un `<model>`

Contiene siempre: link principal (visual, colisión, inercia) + joint.
El bloque `<sensor>` de Gazebo se incluye condicionalmente con `with_sensor` (por defecto `true`).
Cuando `parent_link == "map"` se añade un link anchor vacío antes del sensor link para que `sdformat_urdf` pueda resolver el árbol TF en modo standalone.

| Variable | Descripción |
|----------|-------------|
| `prefix` | Prefijo de nombres (puede ser `''`) |
| `parent_link` | Frame padre (`map` en standalone, link real al inyectar en robot) |
| `x, y, z` | Traslación desde `parent_link` (m) |
| `roll, pitch, yaw` | Rotación desde `parent_link` (rad) |
| `mesh_uri` | URI `file://` de la malla DAE |
| `include_parent_joint` | `true` (defecto) → crea joint y anchor link; `false` → solo el link del sensor |
| `with_sensor` | `true` (defecto) → incluye sensor Gazebo; `false` → solo estructura para RSP |
| `namespace` | Namespace ROS 2 del topic *(solo si with_sensor=true)* |
| `angle_min/max` | Ángulos de barrido (deg) *(solo si with_sensor=true)* |
| `range_min/max` | Límites de rango (m) *(solo si with_sensor=true)* |
| `resolution` | Resolución angular (deg) *(solo si with_sensor=true)* |
| `frequency` | Tasa de actualización (Hz) *(solo si with_sensor=true)* |
| `use_gpu` | `gpu_lidar` si True, `lidar` cpu si False *(solo si with_sensor=true)* |
| `noise_enabled` | Activar ruido gaussiano *(solo si with_sensor=true)* |

### `world.sdf.j2` — mundo Gazebo o modelo standalone

| Flag | Default | Efecto |
|------|---------|--------|
| `model_only` | `false` | `true` → `<sdf><model>` para RSP; `false` → `<sdf><world>` completo con sensor horneado |
| `gui` | `true` | Incluye bloque `<gui>` con todos los plugins *(solo si model_only=false)* |
| `with_sensor` | `false` | Incluye bloque sensor Gazebo *(solo si model_only=true)* |
| `with_plugin` | `false` | Añade `gz-sim-sensors-system` a nivel modelo *(solo si model_only=true)* |

---

## Inyección en la Simulación de un Robot Padre

### Opción A — via `IncludeLaunchDescription`

El robot padre incluye este launch completo:

```python
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

sick_share = get_package_share_directory('caddy_ai2_ros2_sensors_lidar_sick_lms_291')

IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        os.path.join(sick_share, 'bringup', 'launch', 'general.launch.py')
    ),
    launch_arguments={
        'sim':         'true',
        'rviz':        'false',
        'prefix':      'front_',
        'namespace':   'robot1',
        'parent_link': 'base_link',
        'x':    '0.30',
        'z':    '0.50',
        'yaw':  '0.0',
        'use_gpu': 'true',
    }.items(),
)
```

### Opción B — inyección del fragmento SDF en el modelo del robot padre

El paquete expone el helper `sick_lms_291_description.py` en `bringup/launch/`
con la función `get_sensor_sdf()` que devuelve el fragmento SDF renderizado listo
para insertar dentro del `<model>` del robot padre.

#### 1. Declarar la dependencia en `package.xml` del robot padre

```xml
<exec_depend>caddy_ai2_ros2_sensors_lidar_sick_lms_291</exec_depend>
```

#### 2. Importar y llamar desde el launch del robot padre

El `sys.path.insert` debe hacerse **dentro** de `_launch()` / `OpaqueFunction`,
no a nivel de módulo, para que `get_package_share_directory` se ejecute cuando
el entorno ROS ya está inicializado.

```python
import sys
import os
from ament_index_python.packages import get_package_share_directory
from launch.actions import OpaqueFunction

def _launch(context, *args, **kwargs):
    sick_share = get_package_share_directory('caddy_ai2_ros2_sensors_lidar_sick_lms_291')
    sys.path.insert(0, os.path.join(sick_share, 'bringup', 'launch'))
    from sick_lms_291_description import get_sensor_sdf

    sensor_fragment = get_sensor_sdf(
        prefix='front_',
        parent_link='base_link',   # link real del robot padre (ya existe en el modelo)
        x=0.30, y=0.0, z=0.50,
        roll=0.0, pitch=0.0, yaw=0.0,
        with_sensor=True,
        namespace='robot1',
        use_gpu=True,
        # noise_enabled=None → lee sensor_params.yaml automáticamente
    )

    # Insertar el fragmento en el template SDF del robot padre
    robot_sdf = robot_env.get_template('robot.sdf.j2').render(
        sick_sensor=sensor_fragment,
        ...
    )
```

#### 3. Insertar el fragmento en el template SDF del robot padre

```xml
{# robot.sdf.j2 #}
<model name="my_robot">
  <link name="base_link">
    ...
  </link>

  {{ sick_sensor }}
</model>
```

**Puntos clave de la inyección:**
- `parent_link='base_link'` — el link padre ya existe en el modelo del robot; NO se crea un link anchor vacío (el anchor `map` solo se añade cuando `parent_link == "map"`)
- `include_parent_joint=True` (defecto) — el fragmento crea el joint `base_link → front_lidar_sick_lms_291_link`
- El robot padre NO debe crear ese joint por su cuenta
- El `frame_id` del scan es `front_lidar_sick_lms_291_link` (con prefix)
- `noise_enabled=None` (defecto) lee el valor de `sensor_params.yaml`

#### Arrancar el nodo del driver desde el launch del robot padre (hardware real)

Cuando el robot padre ya lanza su propio RSP y Gazebo, se puede incluir solo el
nodo driver del sensor usando `sim:=false rsp:=false`:

```python
IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        os.path.join(sick_share, 'bringup', 'launch', 'general.launch.py')
    ),
    launch_arguments={
        'sim':        'false',
        'rviz':       'false',
        'rsp':        'false',   # RSP ya lo lanza el sistema padre
        'namespace':  'robot1',
        'parent_link': 'base_link',
        'x':  '0.30',
        'z':  '0.50',
    }.items(),
)
```

Esto lanza únicamente el `sick_node` con los parámetros de `sensor_params.yaml`.
El TF lo publica el RSP del robot padre, que debe incluir el fragmento del sensor
en su robot description (Opción B, paso 3).

### Topic bridge en el robot padre

```yaml
# gz_msg_bridge.yaml.j2 del paquete host
- ros_topic_name: "{{ ns }}sick_lms_291/scan"
  gz_topic_name:  "/{{ ns }}sick_lms_291/scan"
  ros_type_name:  "sensor_msgs/msg/LaserScan"
  gz_type_name:   "gz.msgs.LaserScan"
  direction:      GZ_TO_ROS
```

### Nota sobre el mesh URI

El patrón `package://` no funciona cuando Gazebo carga el SDF directamente. Usar siempre ruta absoluta `file://` construida en Python:

```python
mesh_uri = f'file://{os.path.join(sick_share, "meshes")}/SICK_LMS291-S05.dae'
```

---

## Dependencias

- **ROS 2 Jazzy:** `rclcpp`, `sensor_msgs`, `geometry_msgs`, `tf2_ros`, `ros_gz_sim`, `ros_gz_bridge`, `robot_state_publisher`
- **Python (launch):** `jinja2`, `pyyaml`
- **Sistema:** `sicktoolbox-1.0.1-patch`, compilador C++14+
- **Construcción:** `ament_cmake`

---

## Recursos Útiles

- [REP 103 — Unidades y convenciones ROS](https://www.ros.org/reps/rep-0103.html)
- [SDFormat 1.11 — sensor/lidar](https://sdformat.org/spec?ver=1.11&elem=sensor#sensor_lidar)
- SickToolbox Quickstart: `doc/code/sicktoolbox-quickstart.pdf`
