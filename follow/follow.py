#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, Imu
from std_msgs.msg import Float64
from rclpy.qos import qos_profile_sensor_data
import math

def euler_from_quaternion(x, y, z, w):
    """將四元數轉換為尤拉角，取得船隻朝向 (Yaw)"""
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)  # 修正了平方的寫法
    return math.atan2(t3, t4)

def gps_to_local(lat, lon, lat0, lon0):
    """將 GPS 座標轉換為以 (lat0, lon0) 為原點的本地直角座標 (公尺)"""
    R = 6371000.0
    x = (lon - lon0) * math.cos(math.radians(lat0)) * math.radians(1) * R
    y = (lat - lat0) * math.radians(1) * R
    return x, y

class FollowerNode(Node):
    def __init__(self):
        super().__init__('follower_node')
        
        # 訂閱 Leader 與 Follower 的 GPS，以及 Follower 的 IMU
        self.leader_gps_sub = self.create_subscription(
            NavSatFix, '/wamv/sensors/gps/gps/fix', self.leader_gps_callback, qos_profile_sensor_data)
        self.follower_gps_sub = self.create_subscription(
            NavSatFix, '/wamv_follower/sensors/gps/gps/fix', self.follower_gps_callback, qos_profile_sensor_data)
        self.follower_imu_sub = self.create_subscription(
            Imu, '/wamv_follower/sensors/imu/imu/data', self.follower_imu_callback, qos_profile_sensor_data)
        
        # 發布推力與轉向指令給 Follower
        self.left_thrust_pub = self.create_publisher(Float64, '/wamv_follower/thrusters/left/thrust', 10)
        self.right_thrust_pub = self.create_publisher(Float64, '/wamv_follower/thrusters/right/thrust', 10)
        self.left_pos_pub = self.create_publisher(Float64, '/wamv_follower/thrusters/left/pos', 10)
        self.right_pos_pub = self.create_publisher(Float64, '/wamv_follower/thrusters/right/pos', 10)
        
        self.leader_gps = None
        self.follower_gps = None
        self.follower_yaw = 0.0
        self.origin_lat = None
        self.origin_lon = None
        
        self.timer = self.create_timer(0.1, self.control_loop)
        self.target_distance = 8.0  # 期望保持的距離 (公尺)
        
        self.get_logger().info("跟隨者節點已啟動，等待 GPS 與 IMU 數據...")

    def leader_gps_callback(self, msg):
        self.leader_gps = msg
        # 以 Leader 收到的第一個 GPS 點作為平面座標的 (0,0) 原點
        if self.origin_lat is None:
            self.origin_lat = msg.latitude
            self.origin_lon = msg.longitude
            self.get_logger().info(f"設定原點: lat={self.origin_lat:.6f}, lon={self.origin_lon:.6f}")

    def follower_gps_callback(self, msg):
        self.follower_gps = msg

    def follower_imu_callback(self, msg):
        q = msg.orientation
        self.follower_yaw = euler_from_quaternion(q.x, q.y, q.z, q.w)

    def control_loop(self):
        if self.leader_gps is None or self.follower_gps is None or self.origin_lat is None:
            return

        # 將經緯度轉為公尺 (X, Y)
        lx, ly = gps_to_local(self.leader_gps.latitude, self.leader_gps.longitude,
                               self.origin_lat, self.origin_lon)
        fx, fy = gps_to_local(self.follower_gps.latitude, self.follower_gps.longitude,
                               self.origin_lat, self.origin_lon)

        # 計算相對距離與角度
        dx = lx - fx
        dy = ly - fy
        distance = math.sqrt(dx**2 + dy**2)
        angle_to_leader = math.atan2(dy, dx)
        
        heading_error = angle_to_leader - self.follower_yaw
        while heading_error > math.pi: heading_error -= 2.0 * math.pi
        while heading_error < -math.pi: heading_error += 2.0 * math.pi
        
        # P 控制器：調整增益以符合 -1.0 到 1.0 的推力範圍
        k_p_linear = 0.15   
        k_p_angular = 0.6  
        
        forward_thrust = 0.0
        if distance > self.target_distance:
            forward_thrust = k_p_linear * (distance - self.target_distance)
            
        turn_thrust = k_p_angular * heading_error
        
        left_cmd = forward_thrust - turn_thrust
        right_cmd = forward_thrust + turn_thrust
        
        # 限制推力在 [-1.0, 1.0] 之間
        left_cmd = max(-1.0, min(1.0, left_cmd))
        right_cmd = max(-1.0, min(1.0, right_cmd))
        
        msg_left = Float64(); msg_left.data = left_cmd
        msg_right = Float64(); msg_right.data = right_cmd
        msg_pos = Float64(); msg_pos.data = 0.0 

        self.get_logger().info(f"距離: {distance:.2f} m, 角度誤差: {math.degrees(heading_error):.1f}°, 左推力: {left_cmd:.2f}, 右推力: {right_cmd:.2f}")
        
        self.left_thrust_pub.publish(msg_left)
        self.right_thrust_pub.publish(msg_right)
        self.left_pos_pub.publish(msg_pos)
        self.right_pos_pub.publish(msg_pos)

def main(args=None):
    rclpy.init(args=args)
    node = FollowerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()