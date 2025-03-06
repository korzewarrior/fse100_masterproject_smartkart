# Smart Kart Installation Guide

This guide provides step-by-step instructions for installing and configuring the Smart Kart system on a Raspberry Pi.

## Hardware Requirements

- Raspberry Pi 4 (with at least 2GB RAM recommended)
- microSD card (16GB minimum, Class 10 recommended)
- Power supply for Raspberry Pi
- HX711 load cell amplifier
- Load cell sensors (weight sensors)
- Camera module (Raspberry Pi Camera or USB webcam)
- RFID reader (MFRC522)
- LCD display (optional)
- Speaker/buzzer for audio feedback
- Buttons for user interaction
- Battery pack (for portable operation)
- Jumper wires, breadboard for prototyping

## Software Requirements

- Raspberry Pi OS (Bullseye or newer)
- Python 3.7 or later
- Required Python packages (included in requirements.txt)

## Hardware Setup

### Wiring Diagram

```
                   +----------+
                   |Raspberry |
                   |   Pi 4   |
                   +-----+----+
                         |
         +---------------+----------------+
         |               |                |
    +----+----+     +----+----+     +----+----+
    | Weight  |     | Camera  |     |  RFID   |
    | Sensor  |     | Module  |     | Reader  |
    +---------+     +---------+     +---------+
```

### Weight Sensor Connection

Connect the HX711 module to the Raspberry Pi:

1. VCC → 5V
2. GND → GND
3. DT → GPIO5 (or as configured in config.yaml)
4. SCK → GPIO6 (or as configured in config.yaml)

Connect the load cells to the HX711 according to your specific load cell's documentation.

### Camera Module Connection

If using the Raspberry Pi Camera:

1. Connect the camera to the CSI port on the Raspberry Pi
2. Enable the camera in Raspberry Pi configuration

If using a USB webcam:

1. Simply connect it to an available USB port

### RFID Reader Connection

Connect the MFRC522 module to the Raspberry Pi:

1. SDA → GPIO8 (SPI CE0)
2. SCK → GPIO11 (SPI SCLK)
3. MOSI → GPIO10 (SPI MOSI)
4. MISO → GPIO9 (SPI MISO)
5. IRQ → Not connected
6. GND → GND
7. RST → GPIO25 (or as configured in config.yaml)
8. 3.3V → 3.3V

## Software Installation

### 1. Install Raspberry Pi OS

1. Download and install the Raspberry Pi Imager from [raspberrypi.org](https://www.raspberrypi.org/software/)
2. Use the imager to install Raspberry Pi OS (32-bit or 64-bit, with desktop) on your microSD card
3. Configure Wi-Fi, SSH, and other options during installation
4. Boot the Raspberry Pi with the prepared microSD card

### 2. Update the System

```bash
sudo apt update
sudo apt upgrade -y
```

### 3. Install Required System Packages

```bash
sudo apt install -y python3-pip python3-dev python3-venv
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y tesseract-ocr libtesseract-dev
sudo apt install -y libportaudio2 portaudio19-dev
sudo apt install -y libatlas-base-dev
sudo apt install -y git
```

### 4. Enable SPI Interface

The RFID reader requires SPI to be enabled:

```bash
sudo raspi-config
```

Navigate to "Interface Options" → "SPI" → Enable → Finish

### 5. Clone the Smart Kart Repository

```bash
git clone https://github.com/yourusername/smartkart.git
cd smartkart
```

### 6. Create a Virtual Environment (Optional but Recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 7. Install Python Requirements

```bash
pip install -r requirements.txt
```

This will install all the required Python packages, including:
- RPi.GPIO for GPIO control
- picamera for camera control
- OpenCV for image processing
- pyzbar for barcode scanning
- Adafruit libraries for sensors
- And other dependencies

## Configuration

Edit the `config.yaml` file to match your hardware setup:

```bash
nano config.yaml
```

Key settings to adjust:

- GPIO pin assignments for your hardware connections
- Camera settings
- Network settings
- Feature toggles

## Testing the Installation

Run the test script to verify that everything is working correctly:

```bash
python test_system.py
```

This will run a simulation that tests all components of the system.

## Running the System

To start the Smart Kart system:

```bash
python src/main.py
```

### Command-line Options

- `-c, --config`: Specify a custom config file (default: config.yaml)
- `-d, --debug`: Enable debug logging
- `-s, --simulation`: Run in simulation mode (no hardware required)

Example:

```bash
python src/main.py -d -c my_custom_config.yaml
```

## Setting Up to Run on Boot

To have the Smart Kart system start automatically when the Raspberry Pi boots:

1. Create a systemd service file:

```bash
sudo nano /etc/systemd/system/smartkart.service
```

2. Add the following content (adjust paths as needed):

```ini
[Unit]
Description=Smart Kart Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smartkart
ExecStart=/home/pi/smartkart/venv/bin/python /home/pi/smartkart/src/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:

```bash
sudo systemctl enable smartkart.service
sudo systemctl start smartkart.service
```

## Troubleshooting

### Weight Sensor Issues

- Make sure the HX711 module is correctly connected
- Calibrate the scale by updating the `reference_unit` value in config.yaml
- Check the wiring and ensure the load cells are properly installed

### Camera Issues

- For the Raspberry Pi Camera, ensure it's enabled in raspi-config
- For USB cameras, check the device path in config.yaml
- Test the camera using the command: `raspistill -o test.jpg`

### RFID Reader Issues

- Verify that SPI is enabled in raspi-config
- Check the wiring connections
- Test the RFID reader using a simple test script

### Permission Issues

If you encounter permission errors:

```bash
sudo usermod -a -G gpio,spi,i2c,video pi
```

Then reboot the Raspberry Pi.

## Further Resources

- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [HX711 Load Cell Amplifier Guide](https://learn.sparkfun.com/tutorials/load-cell-amplifier-hx711-breakout-hookup-guide/all)
- [MFRC522 RFID Guide](https://pimylifeup.com/raspberry-pi-rfid-rc522/)
- [OpenCV Documentation](https://docs.opencv.org/) 