#!/usr/bin/env python3
import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QHBoxLayout, QLabel, QSlider
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence


class WamvTeleopNode(Node):
    def __init__(self, boat_name='wamv'):
        super().__init__('wamv_pyqt_teleop')

        self.boat_name = boat_name

        self.pub_l_pos = self.create_publisher(Float64, f'/{boat_name}/thrusters/left/pos',    10)
        self.pub_r_pos = self.create_publisher(Float64, f'/{boat_name}/thrusters/right/pos',   10)
        self.pub_l_thr = self.create_publisher(Float64, f'/{boat_name}/thrusters/left/thrust', 10)
        self.pub_r_thr = self.create_publisher(Float64, f'/{boat_name}/thrusters/right/thrust',10)

        # 個別左右推力，允許差動轉向
        self.left_thrust  = 0.0
        self.right_thrust = 0.0
        self.angle        = 0.0

    def publish(self):
        pos_msg = Float64(); pos_msg.data = self.angle
        l_msg   = Float64(); l_msg.data   = self.left_thrust
        r_msg   = Float64(); r_msg.data   = self.right_thrust

        self.pub_l_pos.publish(pos_msg)
        self.pub_r_pos.publish(pos_msg)
        self.pub_l_thr.publish(l_msg)
        self.pub_r_thr.publish(r_msg)


class TeleopUI(QWidget):
    def __init__(self, ros_node: WamvTeleopNode):
        super().__init__()
        self.node = ros_node

        self.base_thrust = 500.0   # 預設前進推力
        self.turn_delta  = 300.0   # 轉向差動量

        self.setWindowTitle(f"WAM-V Teleop  [{ros_node.boat_name}]")
        self.setFixedSize(360, 320)
        self.setFocusPolicy(Qt.StrongFocus)   # 讓視窗能接收鍵盤事件

        layout = QVBoxLayout()

        # ── 說明 ───────────────────────────────
        hint = QLabel(
            "鍵盤：W 前進  S 後退  A 左轉  D 右轉  Space 停止\n"
            "也可使用下方按鈕操作"
        )
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        # ── 推力 Slider ───────────────────────
        self.thrust_label = QLabel(f"基礎推力: {int(self.base_thrust)}")
        self.thrust_slider = QSlider(Qt.Horizontal)
        self.thrust_slider.setRange(0, 1000)
        self.thrust_slider.setValue(int(self.base_thrust))
        self.thrust_slider.valueChanged.connect(self.update_thrust)

        layout.addWidget(self.thrust_label)
        layout.addWidget(self.thrust_slider)

        # ── 狀態顯示 ──────────────────────────
        self.status_label = QLabel("L: 0   R: 0   angle: 0.00")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # ── 按鈕 ──────────────────────────────
        fwd_layout = QHBoxLayout()
        self.btn_fwd  = QPushButton("↑ W 前進")
        fwd_layout.addWidget(self.btn_fwd)
        layout.addLayout(fwd_layout)

        mid_layout = QHBoxLayout()
        self.btn_left  = QPushButton("← A 左轉")
        self.btn_stop  = QPushButton("⬛ Space 停止")
        self.btn_right = QPushButton("D 右轉 →")
        mid_layout.addWidget(self.btn_left)
        mid_layout.addWidget(self.btn_stop)
        mid_layout.addWidget(self.btn_right)
        layout.addLayout(mid_layout)

        back_layout = QHBoxLayout()
        self.btn_back = QPushButton("↓ S 後退")
        back_layout.addWidget(self.btn_back)
        layout.addLayout(back_layout)

        self.setLayout(layout)

        # ── 按鈕綁定 ──────────────────────────
        self.btn_fwd.clicked.connect(self.cmd_forward)
        self.btn_back.clicked.connect(self.cmd_backward)
        self.btn_left.clicked.connect(self.cmd_left)
        self.btn_right.clicked.connect(self.cmd_right)
        self.btn_stop.clicked.connect(self.cmd_stop)

        # ── 10 Hz 發布 ────────────────────────
        self.pub_timer = QTimer()
        self.pub_timer.timeout.connect(self._publish_and_update_ui)
        self.pub_timer.start(100)

    # ── 指令函式 ──────────────────────────────
    def cmd_forward(self):
        self.node.left_thrust  =  self.base_thrust
        self.node.right_thrust =  self.base_thrust
        self.node.angle        =  0.0

    def cmd_backward(self):
        self.node.left_thrust  = -self.base_thrust
        self.node.right_thrust = -self.base_thrust
        self.node.angle        =  0.0

    def cmd_left(self):
        self.node.left_thrust  =  self.base_thrust - self.turn_delta
        self.node.right_thrust =  self.base_thrust + self.turn_delta
        self.node.angle        =  0.0

    def cmd_right(self):
        self.node.left_thrust  =  self.base_thrust + self.turn_delta
        self.node.right_thrust =  self.base_thrust - self.turn_delta
        self.node.angle        =  0.0

    def cmd_stop(self):
        self.node.left_thrust  = 0.0
        self.node.right_thrust = 0.0
        self.node.angle        = 0.0

    # ── 鍵盤事件 ──────────────────────────────
    def keyPressEvent(self, event):
        key = event.key()
        if   key == Qt.Key_W: self.cmd_forward()
        elif key == Qt.Key_S: self.cmd_backward()
        elif key == Qt.Key_A: self.cmd_left()
        elif key == Qt.Key_D: self.cmd_right()
        elif key == Qt.Key_Space: self.cmd_stop()

    # ── Slider ────────────────────────────────
    def update_thrust(self, value):
        self.base_thrust = float(value)
        self.thrust_label.setText(f"基礎推力: {value}")

    # ── UI 更新 ───────────────────────────────
    def _publish_and_update_ui(self):
        self.node.publish()
        self.status_label.setText(
            f"L: {self.node.left_thrust:.0f}  "
            f"R: {self.node.right_thrust:.0f}  "
            f"angle: {self.node.angle:.2f}"
        )


def main():
    rclpy.init()
    # 控制 Leader boat (wamv)，Follower (wamv2) 由 follow.py 自動跟隨
    node = WamvTeleopNode(boat_name='wamv')

    app = QApplication(sys.argv)
    ui = TeleopUI(node)
    ui.show()

    ros_timer = QTimer()
    ros_timer.timeout.connect(lambda: rclpy.spin_once(node, timeout_sec=0))
    ros_timer.start(10)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()



class WamvTeleopNode(Node):
    def __init__(self):
        super().__init__('wamv_pyqt_teleop')

        self.pub_l_pos = self.create_publisher(Float64, '/wamv/thrusters/left/pos', 10)
        self.pub_r_pos = self.create_publisher(Float64, '/wamv/thrusters/right/pos', 10)
        self.pub_l_thr = self.create_publisher(Float64, '/wamv/thrusters/left/thrust', 10)
        self.pub_r_thr = self.create_publisher(Float64, '/wamv/thrusters/right/thrust', 10)

        self.thrust = 0.0
        self.angle = 0.0

    def publish(self):
        pos = Float64(); pos.data = self.angle
        thr = Float64(); thr.data = self.thrust

        self.pub_l_pos.publish(pos)
        self.pub_r_pos.publish(pos)
        self.pub_l_thr.publish(thr)
        self.pub_r_thr.publish(thr)


class TeleopUI(QWidget):
    def __init__(self, ros_node: WamvTeleopNode):
        super().__init__()
        self.node = ros_node

        self.setWindowTitle("WAM-V Teleop")
        self.setFixedSize(300, 220)

        layout = QVBoxLayout()

        # Thrust slider
        self.thrust_label = QLabel("Thrust: 0")
        self.thrust_slider = QSlider(Qt.Horizontal)
        self.thrust_slider.setRange(0, 80)
        self.thrust_slider.valueChanged.connect(self.update_thrust)

        layout.addWidget(self.thrust_label)
        layout.addWidget(self.thrust_slider)

        # Direction buttons
        btn_layout = QHBoxLayout()

        self.btn_left = QPushButton("← Left")
        self.btn_right = QPushButton("Right →")
        self.btn_fwd = QPushButton("↑ Forward")
        self.btn_back = QPushButton("↓ Backward")
        self.btn_stop = QPushButton("STOP")

        self.btn_left.clicked.connect(lambda: self.set_angle(-0.5))
        self.btn_right.clicked.connect(lambda: self.set_angle(0.5))
        self.btn_fwd.clicked.connect(lambda: self.set_motion(0.0, +1))
        self.btn_back.clicked.connect(lambda: self.set_motion(0.0, -1))
        self.btn_stop.clicked.connect(self.stop)

        btn_layout.addWidget(self.btn_left)
        btn_layout.addWidget(self.btn_right)

        layout.addLayout(btn_layout)
        layout.addWidget(self.btn_fwd)
        layout.addWidget(self.btn_back)
        layout.addWidget(self.btn_stop)

        self.setLayout(layout)

        # Publish at 10 Hz
        self.timer = QTimer()
        self.timer.timeout.connect(self.node.publish)
        self.timer.start(100)

    def update_thrust(self, value):
        self.node.thrust = float(value)
        self.thrust_label.setText(f"Thrust: {value}")

    def set_angle(self, angle):
        self.node.angle = angle

    def set_motion(self, angle, direction):
        self.node.angle = angle
        self.node.thrust *= direction

    def stop(self):
        self.node.thrust = 0.0
        self.node.angle = 0.0


def main():
    rclpy.init()
    node = WamvTeleopNode()

    app = QApplication(sys.argv)
    ui = TeleopUI(node)
    ui.show()

    # Spin ROS inside Qt loop
    ros_timer = QTimer()
    ros_timer.timeout.connect(lambda: rclpy.spin_once(node, timeout_sec=0))
    ros_timer.start(10)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
