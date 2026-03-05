# VRX
This repo is for ROS2 Jazzy user only!!
And please build from source in your workspace

# Installation

```
mkdir vrx_ws/
cd vrx_ws/
git clone https://github.com/StanleyChueh/vrx.git
```

Please follow the official instruction for detail:

https://github.com/osrf/vrx/wiki/tutorials

# Basic example

This part assume you have built vrx in your workspace

### Launch world

```
cd ~/vrx_ws/
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch vrx_gz competition.launch.py world:=ocean sim_mode:=full
```

Multi-boat import

```
cd ~/vrx_ws/
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch vrx_gz competition.launch.py   world:=ocean   config_file:=$(ros2 pkg prefix vrx_gz --share)/config/two_wamvs.yaml
```

you will see something like this:

<img width="1585" height="857" alt="image" src="https://github.com/user-attachments/assets/95c7fea1-e06b-4f6c-87e8-17640587dc02" />

### RVIZ Visualizarion

```
ros2 launch vrx_gazebo rviz.launch.py
```

### Keyboard control

```
conda deactivate
```

```
cd ~/vrx_ws/src/vrx/keyboard_control/
python3 boat_keyboard_control.py
```

## Envrionment setting

### Wind speed

Please locate ~/vrx_ws/src/vrx/vrx_gz/worlds/sydney_regatta.sdf

Please locate this section
```
<!-- Load the plugin for the wind --> 
<plugin
  filename="libUSVWind.so"
  name="vrx::USVWind">
  <wind_obj>
    <name>wamv</name>
    <link_name>wamv/base_link</link_name>
    <coeff_vector>.5 .5 .33</coeff_vector>
  </wind_obj>
  <!-- Wind -->
  <wind_direction>240</wind_direction>
  <!-- in degrees -->
  <wind_mean_velocity>5.0</wind_mean_velocity>
  <var_wind_gain_constants>0</var_wind_gain_constants>
  <var_wind_time_constants>2</var_wind_time_constants>
  <random_seed>10</random_seed>
  <!-- set to zero/empty to randomize -->
  <update_rate>10</update_rate>
  <topic_wind_speed>/vrx/debug/wind/speed</topic_wind_speed>
  <topic_wind_direction>/vrx/debug/wind/direction</topic_wind_direction>
</plugin>
```

### Wind speed

Please locate ~/vrx_ws/src/vrx/vrx_gz/worlds/sydney_regatta.sdf

Please locate this section

```
    <!-- The wave field -->
    <plugin filename="libPublisherPlugin.so" name="vrx::PublisherPlugin">
      <message type="gz.msgs.Param" topic="/vrx/wavefield/parameters"
               every="2.0">
        params {
          key: "direction"
          value {
            type: DOUBLE
            double_value: 0.0
          }
        }
        params {
          key: "gain"
          value {
            type: DOUBLE
            double_value: 0.3
          }
        }
        params {
          key: "period"
          value {
            type: DOUBLE
            double_value: 5
          }
        }
        params {
          key: "steepness"
          value {
            type: DOUBLE
            double_value: 0
          }
        }
      </message>
    </plugin>
```

##  ASV_WAVE_SIM

For more realistic wave,ocean view, please refer to asv_wave_sim

https://github.com/srmainwaring/asv_wave_sim.git

<img width="1835" height="884" alt="image" src="https://github.com/user-attachments/assets/c82a63f5-998d-48d2-95f6-dbc0b7a48a4a" />

Kill all servers first

```
killall -9 gz-sim-server gz-sim-gui ruby
```

Server

```
source ~/gz_ws/install/setup.bash
export GZ_SIM_RESOURCE_PATH=~/gz_ws/src/asv_wave_sim/gz-waves-models/models:~/gz_ws/src/asv_wave_sim/gz-waves-models/world_models
export GZ_SIM_SYSTEM_PLUGIN_PATH=~/gz_ws/install/lib
# Note: Server doesn't usually need the NVIDIA offload, but it needs the plugin paths.
gz sim -v4 -s -r ~/gz_ws/src/asv_wave_sim/gz-waves-models/worlds/waves.sdf
```


Client

```
source ~/gz_ws/install/setup.bash

# Tell Gazebo where your compiled waves plugins are
export GZ_SIM_SYSTEM_PLUGIN_PATH=$GZ_SIM_SYSTEM_PLUGIN_PATH:~/gz_ws/install/lib

# Keep your existing library and rendering exports
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/ros/jazzy/opt/gz_ogre_next_vendor/lib:/opt/ros/jazzy/opt/gz_rendering_vendor/lib
export GZ_RENDERING_BACKEND=ogre2

# Launch with NVIDIA offload
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia gz sim -v4 -g
```

## Reference

If you use the VRX simulation in your work, please cite our summary publication, [Toward Maritime Robotic Simulation in Gazebo](https://wiki.nps.edu/display/BB/Publications?preview=/1173263776/1173263778/PID6131719.pdf):

```
@InProceedings{bingham19toward,
  Title                    = {Toward Maritime Robotic Simulation in Gazebo},
  Author                   = {Brian Bingham and Carlos Aguero and Michael McCarrin and Joseph Klamo and Joshua Malia and Kevin Allen and Tyler Lum and Marshall Rawson and Rumman Waqar},
  Booktitle                = {Proceedings of MTS/IEEE OCEANS Conference},
  Year                     = {2019},
  Address                  = {Seattle, WA},
  Month                    = {October}
}
```
