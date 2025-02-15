#!/usr/bin/env python3
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch.conditions import IfCondition, UnlessCondition
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node

def generate_launch_description():
    # Declare launch arguments (equivalent to <arg> tags in ROS1)
    paused_arg = DeclareLaunchArgument('paused', default_value='false', description='Start paused')
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='true', description='Use simulation time')
    gui_arg = DeclareLaunchArgument('gui', default_value='true', description='Enable GUI')
    headless_arg = DeclareLaunchArgument('headless', default_value='false', description='Headless mode')
    debug_arg = DeclareLaunchArgument('debug', default_value='false', description='Debug mode')

    # Launch configurations to use in substitutions
    paused = LaunchConfiguration('paused')
    use_sim_time = LaunchConfiguration('use_sim_time')
    gui = LaunchConfiguration('gui')
    headless = LaunchConfiguration('headless')
    debug = LaunchConfiguration('debug')

    # Get share directories for packages
    gazebo_ros_share = get_package_share_directory('gazebo_ros')
    piper_description_share = get_package_share_directory('piper_description')

    # Define the world file path.
    # (Note: ROS1 used "$(find piper_description)/worlds/empty.world" which becomes:)
    world_path = os.path.join(piper_description_share, 'worlds', 'empty.world')

    # Include the empty_world launch file from gazebo_ros.
    # In ROS2 the file is typically named empty_world.launch.py
    empty_world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_share, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world_name': world_path,
            'debug': debug,
            'gui': gui,
            'paused': paused,
            'use_sim_time': use_sim_time,
            'headless': headless
        }.items()
    )
    # Publish the joint state values for the non-fixed joints in the URDF file.
    joint_state_publisher_cmd = Node(
        condition=UnlessCondition(gui),
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher')
    
    # A GUI to manipulate the joint state values
    joint_state_publisher_gui_node = Node(
        condition=IfCondition(gui),
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui')        

    # Process the URDF via xacro.
    # The ROS1 command "$(find xacro)/xacro --inorder '$(find piper_description)/urdf/piper_description.xacro'" 
    # becomes:
    xacro_file = os.path.join(piper_description_share, 'urdf', 'piper_description.urdf.xacro')
    robot_description_content = Command(['xacro ', xacro_file])
    
    # It is common in ROS2 to load the robot_description parameter via robot_state_publisher.
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        # emulate_tty=True,
        remappings=[('/joint_states', '/piper_description/joint_states')],
        parameters=[{'use_sim_time': use_sim_time,
                     'robot_description': robot_description_content}]
    )

    # Spawn the URDF model in Gazebo.
    # In ROS1 this was done with a node running spawn_model with args "-urdf -model arm -param robot_description"
    # In ROS2, the equivalent (using the spawn_entity.py node) is:
    
    spawn_entity_node = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='urdf_spawner',
        output='screen',
        arguments=['-entity', 'arm',
                   '-x', '0.0',
                   '-y', '0.0',
                   '-z', '0.0',
                   '-topic', 'robot_description']
    )
    rviz_config_dir = os.path.join(piper_description_share, 'rviz', 'rviz.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz_node',
        output='screen',
        parameters=[{'use_sim_time': True}],
        arguments=['-d', rviz_config_dir]
    )

    ld = LaunchDescription()

    # Add declared arguments
    ld.add_action(paused_arg)
    ld.add_action(use_sim_time_arg)
    ld.add_action(gui_arg)
    ld.add_action(headless_arg)
    ld.add_action(debug_arg)

    # Add the included launch file and nodes to the launch description
    # ld.add_action(empty_world_launch)
    ld.add_action(joint_state_publisher_cmd)
    ld.add_action(joint_state_publisher_gui_node)
    ld.add_action(robot_state_publisher_node)
    # ld.add_action(spawn_entity_node)
    ld.add_action(rviz_node)

    return ld
