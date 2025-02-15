#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Get share directory for piper_description package.
    piper_description_share = get_package_share_directory('piper_description')
    # Path to the controller configuration YAML file.
    param_file = os.path.join(piper_description_share, 'config', 'piper_gazebo_control.yaml')
    xacro_file = os.path.join(piper_description_share, 'urdf', 'piper_description.xacro')
    robot_description = Command(['xacro ', xacro_file])
    # List of controllers to spawn.
    controllers = [
        'joint_state_controller',
        'joint1_position_controller',
        'joint2_position_controller',
        'joint3_position_controller',
        'joint4_position_controller',
        'joint5_position_controller',
        'joint6_position_controller',
        'joint7_position_controller',
        'joint8_position_controller'
    ]

    return LaunchDescription([
        # Controller spawner node.
        Node(
            package='controller_manager',
            executable='spawner',
            name='controller_spawner',
            namespace='/piper_description',
            output='screen',
            arguments=controllers,
            parameters=[param_file],
            respawn=False
        ),
        # Robot state publisher node with topic remapping.
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            remappings=[('/joint_states', '/piper_description/joint_states')],
            respawn=False,
            parameters=[{'robot_description': robot_description}]
        )
    ])