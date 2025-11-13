from api import EarthRoverMini
import time

def move_forward(api, duration = 1.0):
    print('Moving forward ...')
    start = time.time()
    while time.time() - start < duration:
        api.ctrl_packet(20, 0)
        time.sleep(0.1)
    print('Stop')
    # send_ctl_cmd(sock, 0, 0)

# def move_backward(api, duration = 3.0):
#     print('Moving backward ...')
#     start = time.time()
#     while time.time() - start < duration:
#         send_ctl_cmd(sock, -100, 0)
#         time.sleep(0.1)
#     print('Stop')
#     send_ctl_cmd(sock, 0, 0)

# def change_angle(api, duration = 3.0):
#     print('Changing angle ...')
#     start = time.time()
#     while time.time() - start < duration:
#         send_ctl_cmd(sock, 60, 360)
#         time.sleep(0.1)
#     print('Stop')
#     send_ctl_cmd(sock, 0, 0)

# def robot_move(api, duration=3.0, speed=60, angular=0):
#     print('Moving ...')
#     start = time.time()
#     while time.time() - start < duration:
#         send_ctl_cmd(sock, speed, angular)
#         time.sleep(0.1)
#     print('Stop')
#     send_ctl_cmd(sock, 0, 0)

if __name__ == "__main__":
    rover_ip = "192.168.11.1"
    rover_port = 8888
    apiObj = EarthRoverMini(rover_ip, rover_port)    

    try:
        input("Press enter to move forward...")
        move_forward(apiObj, duration=1.0)
        
        # input("Press enter to move backward...")
        # move_backward(sock)

        # input("Press enter to change angle...")
        # change_angle(sock)

    finally:
        apiObj.disconnect
        print('Connection closed')
