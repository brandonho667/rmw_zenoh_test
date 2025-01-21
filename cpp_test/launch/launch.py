
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import yaml
import os

def generate_launch_description():
    # Create an empty LaunchDescription
    launch_description = LaunchDescription()

    # Generate 50 talker and listener pairs with unique topic names
    for i in range(50):
        talker_node = Node(
            package='cpp_pubsub',
            executable='talker',
            output='screen',
            name=f'talker_{i}',
            parameters=[{'topic_name': f'/topic_{i}'}]  # Unique topic name for each talker
        )

        listener_node = Node(
            package='cpp_pubsub',
            executable='listener',
            output='screen',
            name=f'listener_{i}',
            parameters=[{'topic_name': f'/topic_{i}'}]  # Listener listens to the same unique topic
        )

        # Add the nodes to the launch description
        launch_description.add_action(talker_node)
        launch_description.add_action(listener_node)

    return launch_description
