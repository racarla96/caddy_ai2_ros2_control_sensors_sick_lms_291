#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>
#include <fstream>
#include <sicklms-1.0/SickLMS.hh>
#include <chrono>

using namespace SickToolbox;

class SickNode : public rclcpp::Node {
/**
 * @brief Represents a node that publishes simulated laser scan data.
 */
private:
    std::string port = "/dev/ttyUSB0"; /**< The port used for communication. */
    int baudrate = 38400; /**< The baudrate for communication. */
    std::string frame_id = "laser_frame"; /**< The frame ID for the laser scan data. */
    double resolution = 0.25; /**< The resolution of the laser scan data. */
    bool auto_reconnect = true; /**< Flag indicating whether to automatically reconnect. */
    double angle_max = 90.0; /**< The maximum angle of the laser scan data. */
    double angle_min = -90.0; /**< The minimum angle of the laser scan data. */
    double max_range = 80.0; /**< The maximum range of the laser scan data. */
    double min_range = 0.01; /**< The minimum range of the laser scan data. */
    double frequency = 5.0; /**< The frequency of publishing the laser scan data. */
    sensor_msgs::msg::LaserScan scan; /**< The laser scan data. */
    SickLMS::sick_lms_baud_t desired_baud = SickLMS::SICK_BAUD_38400;
    SickLMS *sick_lms = NULL; /**< The SickLMS object. */
    unsigned int num_range_values;
    unsigned int num_reflect_values;
    unsigned int range_values[SickLMS::SICK_MAX_NUM_MEASUREMENTS] = {0};
    unsigned int reflect_values[SickLMS::SICK_MAX_NUM_MEASUREMENTS] = {0};  
    float cm2m = 0.01; /**< Conversion factor from centimeters to meters. */
    float deg2rad = M_PI / 180.0; /**< Conversion factor from degrees to radians. */
     
    int size_values;
    std::shared_ptr<sensor_msgs::msg::LaserScan> scan_msg = std::make_shared<sensor_msgs::msg::LaserScan>();
    rclcpp::Publisher<sensor_msgs::msg::LaserScan>::SharedPtr laser_pub_;
    rclcpp::TimerBase::SharedPtr timer_;

    void readAndPublishData()
    {
        try {
      	    sick_lms->GetSickScan(range_values, num_range_values);

            scan_msg->header.stamp = this->get_clock()->now();

            for(int i = 0; i < size_values; i++) {
                scan_msg->ranges[i] = ((float) range_values[i]) * this->cm2m;
            }

            laser_pub_->publish(*scan_msg);
        } catch(...) {
            RCLCPP_ERROR(this->get_logger(), "Failed to get scan");
        }
    }


public:
    /**
     * @brief Constructor for the SickNode class.
     */
    SickNode(const rclcpp::NodeOptions &options) : Node("sick_node", options)
    {
        this->declare_parameter("port", port);
        this->get_parameter("port", port);

        this->declare_parameter("frame_id", frame_id);
        this->get_parameter("frame_id", frame_id);

        this->declare_parameter("baudrate", baudrate);
        this->get_parameter("baudrate", baudrate);

        this->declare_parameter("resolution", resolution);
        this->get_parameter("resolution", resolution);

        this->declare_parameter("angle_max", angle_max);
        this->get_parameter("angle_max", angle_max);

        this->declare_parameter("angle_min", angle_min);
        this->get_parameter("angle_min", angle_min);

        this->declare_parameter("max_range", max_range);
        this->get_parameter("max_range", max_range);

        this->declare_parameter("min_range", min_range);
        this->get_parameter("min_range", min_range);

        this->declare_parameter("frequency", frequency);
        this->get_parameter("frequency", frequency);

        if (frequency < 5) {
            frequency = 5.0;
        }

        if (frequency > 75) {
            frequency = 75;
        }

        if (angle_max < angle_min) {
            double temp = angle_max;
            angle_max = angle_min;
            angle_min = temp;
        }

        sick_lms = new SickLMS(port);
        if ((desired_baud = SickLMS::StringToSickBaud(std::to_string(baudrate))) == SickLMS::SICK_BAUD_UNKNOWN) {
            RCLCPP_ERROR(this->get_logger(), "Invalid baud value! Valid values are: 9600, 19200, 38400, and 500000");
        }
        /* Initialize the device */
        try {
            sick_lms->Initialize(desired_baud);
        } catch(...) {
            RCLCPP_ERROR(this->get_logger(), "Initialize failed! Are you using the correct device path?");
        }

        /* Initialize the device */
        try {
            sick_lms->Initialize(desired_baud);
        } catch(...) {
            RCLCPP_ERROR(this->get_logger(), "Initialize failed! Are you using the correct device path?");
        }

        sick_lms_scan_resolution_t res = sick_lms->DoubleToSickScanResolution(resolution);
        if(res == SickLMS::SICK_SCAN_RESOLUTION_UNKNOWN){
            RCLCPP_ERROR(this->get_logger(), "Invalid resolution value! Valid values are: 0.25, 0.5, 1.0");            
        }
        sick_lms->SetSickVariant(SickLMS::SICK_SCAN_ANGLE_180, res);

        scan_msg->header.frame_id = frame_id;
        scan_msg->angle_min = angle_min * deg2rad;
        scan_msg->angle_max = angle_max * deg2rad;
        scan_msg->angle_increment = resolution * deg2rad;
        scan_msg->range_min = min_range;
        scan_msg->range_max = max_range;
        scan_msg->scan_time = 1.0 / frequency;

        size_values = (angle_max - angle_min)/ resolution + 1;
        scan_msg->ranges.resize(size_values);

        // Crear el publicador
        laser_pub_ = this->create_publisher<sensor_msgs::msg::LaserScan>("scan", 1);

        // Publicar los datos cada segundo
        timer_ = this->create_wall_timer(std::chrono::duration<double>(1.0 / frequency), std::bind(&SickNode::readAndPublishData, this));
    }

    ~SickNode() {
        // Perform explicit cleanup if necessary
        RCLCPP_INFO(this->get_logger(), "SickNode destructor called, performing cleanup.");
        sick_lms->Uninitialize();
    }

};



int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::NodeOptions options;
    rclcpp::spin(std::make_shared<SickNode>(options));
    rclcpp::shutdown();
    return 0;   

}