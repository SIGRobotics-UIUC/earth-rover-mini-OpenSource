# Earth Rover Mini+ Host Development

## Build Example
```
git clone --recursive https://github.com/SIGRobotics-UIUC/earth-rover-mini-OpenSource.git
cd earth-rover-mini-OpenSource/Software/Linux
mkdir build
cd build
cmake -DCMAKE_TOOLCHAIN_FILE=../toolchain.cmake ..
make
```

## Connect to Robot
- Install ADB on your development platform
- Search and connect the wireless network <b>frodobot_xxx</b>. The default password is <b>12345678</b>.
- Once the connection is established. Connect to your robot with adb
```bash
adb connect 192.168.11.1:5555
adb shell
```

## Push files to Robot (Optional)
- Once connected via ADB and before running shell, run the following to push a new tcp_bridge file (only if you have modified it) or any other file
- After compiling **bridge.c**, **tcp_bridge** will be present in Software/Linux/build
- cd into the build folder and run the following
```bash
adb push tcp_bridge /data/
```

# Host Control Instructions

This section provides instructions on how to control the robot from a host computer for development and testing purposes.

---

## TCP Control Mechanism Demo w/ Move

The robot has been configured such that it is possible to send commands via TCP and Python. To do this, first navigate to the **/data** folder inside the robot shell and then run the **tcp_bridge** executable by calling `./tcp_bridge`. This sets a TCP receiver connection on the robot side so it is ready to receive the packets sent from external code. You should see some sort of confirmation message that this worked.

Next, go to the **/src/Examples** folder and run the **move.py** script by running `python3 move.py`. This is some basic code that mirrors **move.cpp** but instead in Python. You should see the rover move if you execute this part right. 

I'll now explain how some of this works internally. The script **uart_cp.py** was created as an API for the C structs defined in **ucp.h**. By translating the alignments and the types correctly, can call these Python classes in the same way the C structs were earlier. You can see that the two move files have very similar structure because of this. Another thing that's important is to ensure that the right IP address and port are being used, or else the communication between computer and robot will not happen. If you wish to change these values or you aren't happy with the way the robot handles the connection, you must modify the **bridge.c** file, cmake and make, and then **adb push** the resultant **tcp_bridge** executable into the right folder of the robot, and then run the executable again from the robot side.

*Problems/Notes*
This is all reliant on the IP address and port being constant, which makes it vulnerable to being hacked. Idk what to do about this.\nI tested this out on my dual-boot computer with x86 processors. Not sure how well this would work on ARM chip computers.

## Control Mechanism

The robot is controlled via a **serial interface** using the custom **UART Control Protocol (UCP)** defined in `applications/ucp.h`.  
By sending formatted data packets to the robot's `uart3` port, you can:

- Control movement  
- Trigger calibration routines  
- Receive telemetry  

---

## Serial Port Settings

- **Baud Rate:** 115200  
- **Data Bits:** 8  
- **Parity:** None  
- **Stop Bits:** 1  

---

## Teleoperation (Manual Control)

To manually control the robot, send **`UCP_MOTOR_CTL` (ID: 0x02)** packets.  
These packets contain the desired **linear** and **angular velocity**.

---

## Control Packet Structure (`ucp_ctl_cmd_t`)

The command packet is composed of a **header**, a **payload**, and a **CRC checksum**.  
The **motor control payload** is defined as follows:

| Field     | Type      | Description                                                                 |
|-----------|-----------|-----------------------------------------------------------------------------|
| `hd`      | `ucp_hd_t`| UCP Header (contains length, ID=0x02, index)                                |
| `speed`   | `int16_t` | Desired linear velocity. Positive = forward, negative = backward. Range: -100 to 100. |
| `angular` | `int16_t` | Desired angular velocity. Positive = right, negative = left. Range: -100 to 100. |
| `front_led` | `int16_t` | Controls the front LEDs (not fully implemented).                          |
| `back_led`  | `int16_t` | Controls the back LEDs (not fully implemented).                           |
| `...`       | `...`     | Reserved fields.                                                          |

---

## Getting Started: A Simple Teleop Example

Look to `src/examples/move.cpp`

# Camera Example

## Getting Started: Dual Camera Streaming Over RTSP

Look to `src/Examples/sample_demo_dual_camera.c`
#### Run the example code on the Earth Rover Mini
- Build Examples
- Push `sample_demo_dual_camera` to device via ADB
```
adb push sample_demo_dual_camera /tmp/
```
- Run example
```
adb shell /tmp/sample_demo_dual_camera -s 0 -W 1920 -H 1080 -w 720 -h 576 -f 30 -r 0 -s 1 -W 1920 -H 1080 -w 720 -h 576 -f 30 -r 0 -n 1 -b 1

but for hasan:
sudo -E /mnt/c/Users/Hasan/OneDrive/Desktop/SIGRobotics/platform-tools-latest-windows/platform-tools/adb.exe shell /tmp/sample_demo_dual_camera -s 0 -W 1920 -H 1080 -w 720 -h 576 -f 30 -r 0 -s 1 -W 1920 -H 1080 -w 720 -h 576  -f 30 -r 0 -n 1 -b 1
```
#### Capture video from the Earth Rover Mini camera on the computer
- go to the **/src/Examples** folder
- run the camera script:
```
python3 camera.py
```
This will open a window displaying the real-time video stream from the Earth Rover Mini’s onboard camera.


# Remote Teleoperation
The Earth Rover Mini comes with a 4G module and we provide a network stack that allows you to drive your Earth Rover from anywhere.

## Connecting via FrodoBots Website
1. [Activate your robot](https://discord.com/invite/N7vEWB6Jdu)
2. Click <b>[+ Activate an Earth Rover]</b> on the [my.frodobots](https://my.frodobots.com/) to link your Earth Rover.
3. Start driving your Earth Rover.

## Connecting via Earth Rover SDK
1. Follow the instructions in <b>Connecting via FrodoBots Website</b> to activate and link your Earth Rover.
2. Go to <b>Settings</b> on [my.frodobots](https://my.frodobots.com/), find your <b>SDK Access Token</b>, and copy it.
3. Install the SDK:
```bash
git clone https://github.com/frodobots-org/earth-rovers-sdk.git
cd earth-rovers-sdk
pip3 install -r requirements.txt
```
4. Create a <b>.env</b> file in the earth-rovers-sdk directory and update it with your token.
```
SDK_API_TOKEN="<Your SDK Access Token>"
#  example: zero-inlay-cal
BOT_SLUG="<Your Bot name>"
```
5. Run the SDK
```bash
hypercorn main:app --reload
```
6. Now you can check the live streaming of the bot in the following URL: [http://localhost:8000](http://localhost:8000/)


### More API Information
Visit the SDK [repository](https://github.com/frodobots-org/earth-rovers-sdk) for more API information.

### Need Support?
Visit the [FrodoBots Discord](https://discord.gg/3pJmcDRh) for help.
