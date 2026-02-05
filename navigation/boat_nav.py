#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node

from std_msgs.msg import Float64
from sensor_msgs.msg import NavSatFix, Imu
from geometry_msgs.msg import PoseStamped

def quat_to_yaw(qx, qy, qz, qw) -> float:
    """Return yaw (rad) from quaternion. Assumes ENU frame, yaw about +Z."""
    # yaw (z-axis rotation)
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)

def wrap_pi(a: float) -> float:
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a

class WamvWaypointNav(Node):
    def __init__(self):
        super().__init__('wamv_waypoint_nav')

        # Publishers (VRX typically uses Float64)
        self.pub_l_pos = self.create_publisher(Float64, '/wamv/thrusters/left/pos', 10)
        self.pub_r_pos = self.create_publisher(Float64, '/wamv/thrusters/right/pos', 10)
        self.pub_l_thr = self.create_publisher(Float64, '/wamv/thrusters/left/thrust', 10)
        self.pub_r_thr = self.create_publisher(Float64, '/wamv/thrusters/right/thrust', 10)

        # Subscribers
        self.create_subscription(NavSatFix, '/wamv/sensors/gps/gps/fix', self.cb_gps, 10)
        self.create_subscription(Imu, '/wamv/sensors/imu/imu/data', self.cb_imu, 10)

        # GPS goal subscriber
        self.create_subscription(NavSatFix, '/gps_goal', self.cb_goal, 10)

        # State
        self.have_ref = False
        self.lat0 = None
        self.lon0 = None
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        self.have_goal = False
        self.goal_lat = None
        self.goal_lon = None

        # Parameters (tune here)
        self.max_thrust = 80.0          # N (VRX-safe-ish starting point)
        self.max_pos = 0.6              # rad thruster angle limit
        self.kp_heading = 1.5           # heading error -> thruster angle
        self.kp_speed = 30.0            # distance -> thrust
        self.slow_radius = 8.0          # m, start slowing down when close
        self.stop_radius = 2.0          # m, stop when within this

        # Timer control loop
        self.dt = 0.1
        self.create_timer(self.dt, self.loop)

        self.get_logger().info(
            "WAM-V Waypoint Nav started.\n"
            "Sub: /wamv/sensors/gps/gps/fix, /wamv/sensors/imu/imu/data, /goal_pose\n"
            "Pub: /wamv/thrusters/* (Float64)\n"
            "Send a goal to /goal_pose (PoseStamped x,y in local frame)."
        )

    def cb_gps(self, msg: NavSatFix):
        if msg.status.status < 0:
            return
        lat = msg.latitude
        lon = msg.longitude

        # Set reference origin at first valid fix
        if not self.have_ref:
            self.lat0 = lat
            self.lon0 = lon
            self.have_ref = True
            self.get_logger().info(f"Set local GPS reference lat0={self.lat0:.8f}, lon0={self.lon0:.8f}")

        # Convert lat/lon to local meters (equirectangular approximation)
        # Good enough for small VRX worlds.
        R = 6378137.0  # Earth radius (m)
        lat0_rad = math.radians(self.lat0)
        dlat = math.radians(lat - self.lat0)
        dlon = math.radians(lon - self.lon0)

        self.x = R * dlon * math.cos(lat0_rad)  # East
        self.y = R * dlat                       # North

    def cb_imu(self, msg: Imu):
        q = msg.orientation
        self.yaw = quat_to_yaw(q.x, q.y, q.z, q.w)

    # Callback for GPS goal
    def cb_goal(self, msg: NavSatFix):
        if msg.status.status < 0:
            return
        self.goal_lat = msg.latitude
        self.goal_lon = msg.longitude
        self.have_goal = True
        self.get_logger().info(
            f"New GPS goal: lat={self.goal_lat:.8f}, lon={self.goal_lon:.8f}"
        )

    def publish_cmd(self, pos: float, thrust: float):
        mpos = Float64(); mpos.data = float(pos)
        mthr = Float64(); mthr.data = float(thrust)
        self.pub_l_pos.publish(mpos)
        self.pub_r_pos.publish(mpos)
        self.pub_l_thr.publish(mthr)
        self.pub_r_thr.publish(mthr)

    def loop(self):
        # Safety: until GPS reference set and goal received, hold still
        if not self.have_ref or not self.have_goal:
            self.publish_cmd(0.0, 0.0)
            return

        R = 6378137.0
        lat0_rad = math.radians(self.lat0)

        dlat = math.radians(self.goal_lat - self.lat0)
        dlon = math.radians(self.goal_lon - self.lon0)

        gx = R * dlon * math.cos(lat0_rad)
        gy = R * dlat

        dx = gx - self.x
        dy = gy - self.y

        dist = math.hypot(dx, dy)

        if dist < self.stop_radius:
            self.publish_cmd(0.0, 0.0)
            return

        desired_yaw = math.atan2(dy, dx)
        heading_err = wrap_pi(desired_yaw - self.yaw)

        # Thruster angle command (turning)
        pos_cmd = self.kp_heading * heading_err
        pos_cmd = max(-self.max_pos, min(self.max_pos, pos_cmd))

        # Thrust command: proportional to distance, slow down near goal
        if dist < self.slow_radius:
            # ramp down linearly inside slow radius
            thrust_cmd = self.kp_speed * (dist / self.slow_radius)
        else:
            thrust_cmd = self.kp_speed

        thrust_cmd = max(0.0, min(self.max_thrust, thrust_cmd))

        # If heading error is large, reduce forward thrust to avoid wide arcs
        thrust_cmd *= max(0.2, math.cos(heading_err))

        self.publish_cmd(pos_cmd, thrust_cmd)

def main():
    rclpy.init()
    node = WamvWaypointNav()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_cmd(0.0, 0.0)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
