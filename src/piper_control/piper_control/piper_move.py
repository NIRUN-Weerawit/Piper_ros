import rclpy
from rclpy.node import Node

from std_msgs.msg import String, Float64MultiArray

class JointPositionPublisher(Node):
    def __int__(self):
        super().__init__('joint_position_publisher')
        self.pub = self.create_publisher(Float64MultiArray, '/joints_position_controller/commands', 10)
        
        
def main(args=None):
     rclpy.init(args=args)
     
     control_pub = JointPositionPublisher()
     
     rclpy.spin(control_pub)
     
     control_pub.destroy_node()
     rclpy.shutdown()
     
if __name__ == '__main__':
    main()