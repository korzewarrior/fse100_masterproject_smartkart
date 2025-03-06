# Smart Kart

## Overview
Smart Kart is an intelligent shopping cart attachment designed to improve accessibility and ease of shopping. By integrating barcode scanners, RFID readers, weight sensors, and AI-driven product recognition, the Smart Kart enables hands-free scanning and verification of products. The system provides real-time feedback through audio, visual, and haptic outputs to assist users, particularly those with visual impairments or dexterity challenges.

## Key Features
- **Product Scanning**: Barcode/RFID scanning for product identification
- **Inventory Tracking**: Real-time tracking of cart contents
- **Weight Detection**: Load sensors to verify products placed in cart
- **Ingredient Verification**: AI-powered analysis of product labels to identify ingredients
- **User Interface**: Audio and visual feedback for user interaction
- **Simulation Mode**: Test the system without physical hardware

## How It Works
1. As the shopper places an item in the cart, the barcode scanner or RFID reader scans the product.
2. The weight sensor verifies the presence of the item and prevents unscanned items from being placed.
3. The camera module provides additional verification and can recognize unlabeled items using AI.
4. The system provides feedback through a speaker (audible confirmation), buzzer alarm (alerts for errors), and visual display (text-based confirmation).
5. The Smart Kart connects to a mobile app via Wi-Fi, where users can track their purchases and receive notifications.

## Hardware Requirements
- Raspberry Pi 4 (or equivalent)
- Camera module (for barcode scanning)
- RFID reader
- Weight sensors (load cells)
- LCD touch screen display
- Battery pack
- Motion sensors
- Optional: GPS module for precise location tracking

## Software Architecture
The system is organized into the following components:
- **Sensors**: Code for interfacing with various sensors (weight, barcode, RFID)
- **Hardware**: Drivers and interfaces for physical components
- **Controllers**: Business logic for the cart's operation
- **UI**: User interface components
- **Utils**: Common utilities and helper functions

## Implementation Status
- ✅ Project structure and configuration system
- ✅ Weight sensor module
- ✅ Barcode scanner module
- ✅ System controller
- ✅ Ingredient analyzer
- ✅ Simulation mode for testing without hardware
- ⬜ RFID reader module
- ⬜ User interface module
- ⬜ Mobile app integration
- ⬜ AI-based product recognition

## Getting Started
1. Clone the repository
2. Install the required dependencies: `pip install -r requirements.txt`
3. Run the test script to verify the system: `python test_system.py`
4. For a real deployment, follow the instructions in `docs/INSTALLATION.md`

## Running the System
```bash
# Run in simulation mode (no hardware required)
python src/main.py -s

# Run with hardware
python src/main.py

# Run with debug logging
python src/main.py -d
```

## Next Steps
1. Implement the RFID reader module
2. Develop the user interface module
3. Integrate with a mobile app
4. Implement AI-based product recognition
5. Test with actual hardware on a Raspberry Pi
6. Optimize for battery life and performance

## License
[License information to be added]

## Contributors
[Contributors to be added] 