#!/usr/bin/env python3
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch.conditions import IfCondition, UnlessCondition
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node

def generate_launch_description():
    
    paused_arg       = DeclareLaunchArgument('paused',       default_value='false', description='Start paused')
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='true',  description='Use simulation time')
    gui_arg          = DeclareLaunchArgument('gui',          default_value='true',  description='Enable GUI')
    headless_arg     = DeclareLaunchArgument('headless',     default_value='false', description='Headless mode')
    debug_arg        = DeclareLaunchArgument('debug',        default_value='false', description='Debug mode')

    # Launch configurations to use in substitutions
    paused       = LaunchConfiguration('paused')
    use_sim_time = LaunchConfiguration('use_sim_time')
    gui          = LaunchConfiguration('gui')
    headless     = LaunchConfiguration('headless')
    debug        = LaunchConfiguration('debug')

    # Paths 
    gazebo_ros_share        = get_package_share_directory('gazebo_ros')
    piper_description_share = get_package_share_directory('piper_description')
    world_path     = piper_description_share + '/worlds/' + 'empty.world'
    world_ros_path = gazebo_ros_share + '/worlds/empty.world'
    xacro_file = piper_description_share + '/urdf/' + 'piper_description.urdf.xacro'
    robot_description_content = Command(['xacro ', xacro_file])
    rviz_config_dir = os.path.join(piper_description_share, 'rviz', 'rviz.rviz')
    param_file = piper_description_share + '/config/piper_gazebo_control.yaml'
    
    # Laucnhing Gazebo with empty.world
    gazebo_node    = ExecuteProcess(cmd=['gazebo', '--verbose', world_path, '-s', 'libgazebo_ros_factory.so'], output='screen')
    
    # Nodes
    
    # Include the empty_world launch file from gazebo_ros
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
        name='joint_state_publisher',
        parameters=[{'use_sim_time': use_sim_time,
                     'robot_description': robot_description_content}])
    
    # A GUI to manipulate the joint state values (available when joints are defined separately)
    joint_state_publisher_gui_node = Node(
        condition=IfCondition(gui),
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        # parameters= [{'use_sim_time': use_sim_time,
                    #  'robot_description': robot_description_content}]
    )  
    
    # Publish the robot's state
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='both',
        # emulate_tty=True,
        # remappings=[('/joint_states', '/piper_description/joint_states')],
        parameters=[{'use_sim_time': use_sim_time,
                     'robot_description': robot_description_content}]
    )

    # Spawn the URDF model in Gazebo.
    spawn_entity_node = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='urdf_spawner',
        output='screen',
        arguments=['-entity', 'arm',
                   '-topic', 'robot_description']
    )
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz_node',
        output='screen',
        parameters=[{'use_sim_time': True}],
        arguments=['-d', rviz_config_dir]
    )
    
    controllers = [
        'joint_state_broadcaster',
        'joints_position_controller',
        # 'joint1_position_controller',
        # 'joint2_position_controller',
        # 'joint3_position_controller',
        # 'joint4_position_controller',
        # 'joint5_position_controller',
        # 'joint6_position_controller',
        # 'joint7_position_controller',
        # 'joint8_position_controller'
    ]

    # Node for controlling the joints
    controller_spawner_node = Node(
            package='controller_manager',
            executable='spawner',
            name='controller_spawner',
            # namespace='/piper_description',
            output='both',
            arguments=controllers,
            parameters=[param_file],
            respawn=False
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
    # ld.add_action(joint_state_publisher_gui_node)
    ld.add_action(robot_state_publisher_node)
    ld.add_action(spawn_entity_node)
    ld.add_action(gazebo_node)
    ld.add_action(controller_spawner_node)
    # ld.add_action(rviz_node)

    return ld
