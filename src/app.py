import streamlit as st
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from db_client import EmbeddingClient
from llm import get_possible_objects
from vision import run_clip_on_objects, run_vlm
from utils import get_topk_imgs_from_coord_data, get_count_from_coord_data, display_coord_data
from PIL import Image
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Styling and Layout
st.set_page_config(
    page_title="Intelligent Swarm Robotics Interface",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stProgress .st-bo {
        background-color: #3498db;
    }
    .success-message {
        color: #2ecc71;
        font-weight: bold;
    }
    .processing-message {
        color: #3498db;
        font-style: italic;
    }
    .status-panel {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        float: right;
        padding: 0.5rem 1rem;
        border-radius: 20px;
    }
    /* Add styles for logo */
    .logo-img {
        max-width: 200px;  # Adjust size as needed
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Add logo
try:
    logo = Image.open(os.getenv('LOGO_PATH', 'logo.jpeg'))  # Replace with your logo path
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image(logo)
except Exception as e:
    st.error("Unable to load company logo")

class ROS2Interface(Node):
    def __init__(self):
        super().__init__('streamlit_interface')
        self.publisher_ = self.create_publisher(String, 'coordinate_data', 10)
        self.subscription = self.create_subscription(
            String,
            'ros_feedback',
            self.listener_callback,
            10
        )
        self.received_message = ''

    def listener_callback(self, msg):
        self.received_message = msg.data

    def publish(self, coord_data):
        msg = String()
        msg.data = json.dumps(coord_data)
        self.publisher_.publish(msg)

# global value to check if ROS2 is initialized
st.session_state.ros_initialized = False

# Initialize ROS2 only once
if 'ros_node' not in st.session_state:
    with st.spinner("Initializing ROS2 Connection..."):
        if not rclpy.ok():
            rclpy.init()
        st.session_state.ros_node = ROS2Interface()
        st.session_state.ros_initialized = True
        st.success("ROS2 Connection Established!")
else:
    st.session_state.ros_initialized = True

ros_node = st.session_state.ros_node

# Load database
if "db_client" not in st.session_state:
    with st.spinner("Loading Database..."):
        st.session_state.db_client = EmbeddingClient(os.getenv("DB_URL", 'http://localhost:8000'))
        st.success("Database loaded successfully!")

db_client = st.session_state.db_client

# Main UI
st.title("Centralized Intelligence For Dynamic Swarm Navigation")

# Add a toggle button for the status panel
if 'show_status' not in st.session_state:
    st.session_state.show_status = True

# Create a container for the main content
main_container = st.container()

# Add toggle button in the top right
col1, col2 = st.columns([6, 1])
with col2:
    if st.button('📊 Toggle Status'):
        st.session_state.show_status = not st.session_state.show_status

# Create the layout based on status panel visibility
if st.session_state.show_status:
    main_col, status_col = main_container.columns([3, 1])
else:
    main_col = main_container.columns([1])[0]



with main_col:
    st.markdown("""
    ### Welcome to the Swarm Command Center!
    This system allows you to control swarm robots using natural language commands. 
    The robots will understand your instructions and navigate to the specified objects or locations.

    #### How it works:
    1. Enter your command (e.g., "Go to the nearest fire extinguisher")
    2. The system will identify relevant objects
    3. Robots will locate and navigate to the target
""")

    # Text input with placeholder
    prompt = st.text_input(
        "Enter your command",
        placeholder="Example: Find the nearest fire extinguisher and move towards it",
        help="Type a natural language command for the robots"
    )

    if st.button("🚀 Execute Command", type="primary") and prompt:
        st.markdown("### Processing Pipeline")

        try:
            # Step 1: Natural Language Processing
            with st.status("🧠 Understanding your command...", expanded=True) as status:
                objects_json = get_possible_objects(prompt)
                object_list = objects_json['possible_objects']
                # object_list = ['bed', 'dustbin'] # for testing
                st.write("Possible Objects:", ", ".join(object_list))
                status.update(label="✅ Command understood!", state="complete")

            # Step 2: Object Detection
            with st.status("🔍 Locating objects in environment...", expanded=False) as status:
                obj_detection = run_clip_on_objects(object_list, db_client, topk=5)
                # st.write("Located object at:", obj_detection)
                status.update(label="🔍 Identifying objects in the environment...", state="running")
                coord_data = run_vlm(prompt, obj_detection)
                n_objects = get_count_from_coord_data(coord_data)
                st.write("Navigation coordinates:", display_coord_data(coord_data))
                status.update(label=f"✅ {n_objects} Possible objects located!", state="complete")

            # After getting coord_data, display the detected objects
            with st.status("🖼️ Retrieving object images...", expanded=True) as status:
                top_matches = get_topk_imgs_from_coord_data(coord_data, k=4)  # Returns list of (object_name, image_path)

                # Create a container for images
                st.markdown("### Detected Objects")
                image_cols = st.columns(min(len(top_matches), 4))  # Show 4 images per row max

                for idx, (obj_name, image) in enumerate(top_matches):
                    col_idx = idx % 4  # Determine which column to put the image in
                    with image_cols[col_idx]:
                        try:
                            st.image(image, caption=f"{obj_name}", use_container_width=True)
                        except Exception as e:
                            st.error(f"Could not load image for {obj_name}")

                status.update(label="✅ Object images retrieved!", state="complete")

            # Step 4: Robot Command Execution
            with st.status("🤖 Sending commands to robots...", expanded=True) as status:
                ros_node.publish(coord_data)
                status.update(label="✅ Commands sent to robots!", state="complete")

            st.success("🎉 Command successfully processed and sent to robots!")

            # Robot Feedback
            with st.status("📡 Waiting for robots to reach the target...", expanded=True) as status:
                feedback_received = False
                for i in range(os.getenv('WAIT_FOR_GOAL', 120)):  # Wait up to 120 seconds for the robot
                    rclpy.spin_once(ros_node, timeout_sec=1)
                    if ros_node.received_message:
                        status.update(label=f"✅ Robots have reached the target: {ros_node.received_message}", state="complete")
                        feedback_received = True
                        break
                    else:
                        status.update(label="📡 Waiting for robots to reach the target...", state="running")
                if not feedback_received:
                    status.update(label="⚠️ No feedback received from robots within the timeout period.", state="warning")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("Please try again or contact system administrator if the problem persists.")

if st.session_state.show_status:
    with status_col:
        st.markdown("### 🤖 Robot Status")

        # Add a container with a different background color for the status panel
        with st.container():
            st.markdown("""
                <style>
                [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
                    background-color: #f0f2f6;
                    padding: 1rem;
                    border-radius: 10px;
                }
                </style>
            """, unsafe_allow_html=True)

            # System Status
            st.markdown("#### System Status")
            status_indicator = "🟢" if st.session_state.ros_initialized else "🔴"
            st.markdown(f"ROS2 Connection: {status_indicator}")

        if st.button("🔄 Reset Connection"):
            if "db_client" in st.session_state:
                del st.session_state.db_client
            st.session_state.ros_initialized = False
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <small>Intelligent Swarm Robotics System v1.0 | For assistance, contact support</small>
    </div>
    """, unsafe_allow_html=True)