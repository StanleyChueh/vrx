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

## Basic example

This part assume you have built vrx in your workspace

### Launch world

```
cd ~/vrx_ws/
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch vrx_gz competition.launch.py world:=sydney_regatta
```

you will see something like this:

<img width="1585" height="857" alt="image" src="https://github.com/user-attachments/assets/95c7fea1-e06b-4f6c-87e8-17640587dc02" />

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
