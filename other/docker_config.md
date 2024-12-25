## ros2 humble docker setup with gui support (using xrdp)

if accessing host ip from docker
```
curl http://172.17.0.1:8081/v1
```

## docker with gui support
```
# xhost +local:docker
```
1. NVIDIA Container Toolkit installed:
```bash
sudo apt-get install nvidia-container-toolkit -y
```
2. Docker daemon configured to use the NVIDIA runtime:
```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```
## commands
```
docker stats
```

To start xrdp on an already built container
```bash
docker start ros2_humble_rdp_nv

docker exec -it ros2_humble_rdp_nv /bin/bash
service xrdp start
# or try 
# service xrdp restart
su ros_user
```


Container from docker image
```bash
# to save the container state in a new image (works like git) (however, glitchy as saves the state of xrdp leading to issues)
docker commit humble_ros2 test2

# start headless docker container
docker run -d --name ros2_humble \
    --network host \
    --privileged \
    ros2_rdp

# build
docker build -t name .

# to start container from image
docker run -it \
    --name xfce_rdp \
    -p 3342:3391 \
    --security-opt seccomp=unconfined \
    --gpus all \
    --runtime=nvidia \
    --privileged \
    xfce_rdp
```
