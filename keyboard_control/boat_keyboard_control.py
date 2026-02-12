#!/usr/bin/env python3
import sys

# ROS2 imports
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QHBoxLayout, QLabel, QSlider
)
from PyQt5.QtCore import Qt, QTimer


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
