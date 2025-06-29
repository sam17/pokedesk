# Home Display System

A simple web-based display system that shows metrics.soumyadeep.in by default and switches to camera feed when motion is detected via Home Assistant.

## Features

- Displays metrics.soumyadeep.in in fullscreen by default
- Switches to camera feed when motion detected
- Auto-returns to metrics after 30 seconds
- Home Assistant webhook integration

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment Variables

```bash
export HA_TOKEN="your_home_assistant_long_lived_token"
export HA_URL="http://homeassistant.local:8123"
export CAMERA_ENTITY_ID="camera.your_camera"
```

### 3. Run the Server

**Development (with auto-reload):**
```bash
uv sync  # Install watchdog dependency
uv run python dev_server.py
```

**Production:**
```bash
uv run python server.py
```

The display will be available at `http://localhost:8080`

### 4. Configure Home Assistant

Add the automation from `home_assistant_automation.yaml` to your Home Assistant configuration, replacing:
- `binary_sensor.your_camera_motion` with your motion sensor entity
- `YOUR_DISPLAY_IP` with the IP address of your display device
- `camera.your_camera` with your camera entity

## Usage

- Open `http://YOUR_DISPLAY_IP:8080` on your display device
- The screen will show metrics.soumyadeep.in by default
- When Home Assistant detects motion, it will trigger the webhook
- The display switches to camera feed for 30 seconds
- After 30 seconds, it automatically returns to metrics

## API Endpoints

- `GET /` - Main display page
- `POST /webhook/motion` - Webhook for motion detection
- `GET /api/motion-check` - Check current motion status
- `GET /api/camera-stream` - Camera stream proxy