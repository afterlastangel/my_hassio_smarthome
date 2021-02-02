docker run -d --name="home-assistant" -v /opt/project/smarthome/hassio_config:/config --device=/dev/ttyACM0 -v /etc/localtime:/etc/localtime:ro --net=host homeassistant/home-assistant:stable  
