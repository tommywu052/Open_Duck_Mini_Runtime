import time
from typing import List

import numpy as np
import rustypot


class HWI:
    def __init__(self, usb_port="/dev/ttyACM0"):

        # Order matters here
        self.joints = {
            "left_hip_yaw": 20,
            "left_hip_roll": 21,
            "left_hip_pitch": 22,
            "left_knee": 23,
            "left_ankle": 24,
            "neck_pitch": 30,
            "head_pitch": 31,
            "head_yaw": 32,
            "head_roll": 33,
            # "left_antenna": None,
            # "right_antenna": None,
            "right_hip_yaw": 10,
            "right_hip_roll": 11,
            "right_hip_pitch": 12,
            "right_knee": 13,
            "right_ankle": 14,
        }

        self.zero_pos = {
            "left_hip_yaw": 0,
            "left_hip_roll": 0,
            "left_hip_pitch": 0,
            "left_knee": 0,
            "left_ankle": 0,
            "neck_pitch": 0,
            "head_pitch": 0,
            "head_yaw": 0,
            "head_roll": 0,
            # "left_antenna":0,
            # "right_antenna":0,
            "right_hip_yaw": 0,
            "right_hip_roll": 0,
            "right_hip_pitch": 0,
            "right_knee": 0,
            "right_ankle": 0,
        }

        self.init_pos = {
            "left_hip_yaw": 0.002,
            "left_hip_roll": 0.053,
            "left_hip_pitch": -0.63,
            "left_knee": 1.368,
            "left_ankle": -0.784,
            "neck_pitch": 0.0,
            "head_pitch": 0.0,
            "head_yaw": 0,
            "head_roll": 0,
            # "left_antenna": 0,
            # "right_antenna": 0,
            "right_hip_yaw": -0.003,
            "right_hip_roll": -0.065,
            "right_hip_pitch": 0.635,
            "right_knee": 1.379,
            "right_ankle": -0.796,
        }

        # self.joints_offsets = {
        #     "left_hip_yaw": 0.084,
        #     "left_hip_roll": -0.112,
        #     "left_hip_pitch": -0.024,
        #     "left_knee": 0.005,
        #     "left_ankle": -0.09,
        #     "neck_pitch": 0.017,
        #     "head_pitch": 0.114,
        #     "head_yaw": -0.083,
        #     "head_roll": 0.072,
        #     # "left_antenna": 0,
        #     # "right_antenna": 0,
        #     "right_hip_yaw": -0.13499999999999998,
        #     "right_hip_roll": 0.205,
        #     "right_hip_pitch": 0.064,
        #     "right_knee": -0.027999999999999997,
        #     "right_ankle": -0.09799999999999999,
        # }
        # self.joints_offsets = {
        #     "left_hip_yaw": 0.14,
        #     "left_hip_roll": -0.05,
        #     "left_hip_pitch": -0.011,
        #     "left_knee": 0.0,
        #     "left_ankle": -0.107,
        #     "neck_pitch": 0.061,
        #     "head_pitch": 0.108,
        #     "head_yaw": -0.08399999999999999,
        #     "head_roll": 0.063,
        #     "right_hip_yaw": -0.131,
        #     "right_hip_roll": 0.089,
        #     "right_hip_pitch": 0.06799999999999999,
        #     "right_knee": 0.002,
        #     "right_ankle": -0.093,
        # }
        self.joints_offsets = {
            "left_hip_yaw" : 0.082,
            "left_hip_roll" : -0.089,
            "left_hip_pitch" : -0.004,
            "left_knee" : 0.077,
            "left_ankle" : -0.1,
            "neck_pitch" : 0.057,
            "head_pitch" : 0.069,
            "head_yaw" : -0.101,
            "head_roll" : 0.08,
            "right_hip_yaw" : -0.166,
            "right_hip_roll" : 0.115,
            "right_hip_pitch" : 0.089,
            "right_knee" : -0.098,
            "right_ankle" : -0.125
        }

        init_pos_with_offsets = {
            joint: np.rad2deg(pos + self.joints_offsets[joint])
            for joint, pos in self.init_pos.items()
        }

        self.kps = np.ones(len(self.joints)) * 32  # default kp
        self.kds = np.ones(len(self.joints)) * 0  # default kd
        self.low_torque_kps = np.ones(len(self.joints)) * 2

        # self.control = rustypot.FeetechController(
        #     usb_port, 1000000, 100, list(self.joints.values()), list(self.kps), list(init_pos_with_offsets.values())
        # )
        self.io = rustypot.feetech(usb_port, 1000000)

    def set_kps(self, kps):
        self.kps = kps
        self.io.set_kps(list(self.joints.values()), self.kps)
        # self.control.set_new_kps(self.kps)

    def set_kds(self, kds):
        self.kds = kds
        self.io.set_kds(list(self.joints.values()), self.kds)

    def set_kp(self, id, kp):
        # self.kps[id] = kp
        self.io.set_kps([id], [kp])

    def turn_on(self):
        self.io.set_kps(list(self.joints.values()), self.low_torque_kps)
        # self.control.set_new_kps(self.low_torque_kps)
        print("turn on : low KPS set")
        time.sleep(1)

        self.set_position_all(self.init_pos)
        print("turn on : init pos set")

        time.sleep(1)

        self.io.set_kps(list(self.joints.values()), self.kps)
        print("turn on : high kps")

    def turn_off(self):
        self.io.disable_torque(list(self.joints.values()))
        # self.control.disable_torque()

    # def freeze(self):
    #     self.control.freeze()

    def set_position(self, joint_name, pos):
        """
        pos is in radians
        """
        id = self.joints[joint_name]
        pos = pos + self.joints_offsets[joint_name]
        self.io.write_goal_position([id], [pos])
        # self.control.set_new_target([pos])

    def set_position_all(self, joints_positions):
        """
        joints_positions is a dictionary with joint names as keys and joint positions as values
        Warning: expects radians
        """
        ids_positions = {
            self.joints[joint]: position + self.joints_offsets[joint]
            for joint, position in joints_positions.items()
        }

        self.io.write_goal_position(
            list(self.joints.values()), list(ids_positions.values())
        )
        # self.control.set_new_target(list(ids_positions.values()))
        # self.control.goal_positions = list(ids_positions.values())

    def get_present_positions(self, ignore=[]):
        """
        Returns the present positions in radians
        """

        # present_positions = np.deg2rad(
        #     self.control.io.get_present_position(self.joints.values())
        # )
        try:
            present_positions = self.io.read_present_position(list(self.joints.values()))
        except Exception as e:
            print(e)
            return None
        # present_positions = np.deg2rad(self.control.get_present_position())
        present_positions = [
            pos - self.joints_offsets[joint]
            for joint, pos in zip(self.joints.keys(), present_positions)
            if joint not in ignore
        ]
        return np.array(np.around(present_positions, 3))

    def get_present_velocities(self, rad_s=True, ignore=[]):
        """
        Returns the present velocities in rad/s (default) or rev/min
        """
        try:
            present_velocities = self.io.read_present_velocity(list(self.joints.values()))
        except Exception as e:
            print(e)
            return None
        # present_velocities = np.array(self.control.get_current_speed())
        present_velocities = [
            vel
            for joint, vel in zip(self.joints.keys(), present_velocities)
            if joint not in ignore
        ]
        # present_velocities = np.array(
        #     self.control.io.get_present_speed(self.joints.values())
        # )
        # if rad_s:
        #     present_velocities = np.deg2rad(present_velocities)  # rad/s
        return np.array(np.around(present_velocities, 3))

    # def get_present_voltages(self):
    #     return np.array(self.control.io.get_present_voltage(self.joints.values())) * 0.1

    # def get_present_velocities(self, rad_s=True):
    #     """
    #     Returns the present velocities in rad/s (default) or rev/min
    #     """
    #     # rev/min
    #     present_velocities = np.array(
    #         self.control.io.get_present_speed(self.joints.values())
    #     )
    #     if rad_s:
    #         present_velocities = (2 * np.pi * present_velocities) / 60  # rad/s
    #     return np.array(np.around(present_velocities, 3))
