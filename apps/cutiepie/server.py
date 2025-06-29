#!/usr/bin/env python3

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from aiohttp import web, ClientSession
import aiofiles

# Configure logging
import logging.handlers

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('motion_debug.log')

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Set formatter for handlers
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Set levels
console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.DEBUG)

class HomeDisplayServer:
    def __init__(self):
        self.motion_detected = False
        self.motion_timestamp = None
        self.camera_url = None
        self.ha_token = None
        self.ha_url = None
        self.camera_entity_id = None
        self.motion_sensor_entity_id = None
        self.last_motion_state = "off"
        
        # Load config
        self.load_config()
        
        # Polling task will be started later
        self._polling_task = None
    
    def load_config(self):
        """Load configuration from environment or config file"""
        import os
        from pathlib import Path
        
        # Load .env file if it exists
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
        
        self.ha_token = os.getenv('HA_TOKEN')
        self.ha_url = os.getenv('HA_URL', 'http://homeassistant.local:8123')
        self.camera_entity_id = os.getenv('CAMERA_ENTITY_ID')
        self.motion_sensor_entity_id = os.getenv('MOTION_SENSOR_ENTITY_ID')
        
        logger.info(f"Loaded config - HA URL: {self.ha_url}, Camera: {self.camera_entity_id}, Motion: {self.motion_sensor_entity_id}")
    
    async def webhook_motion(self, request):
        """Webhook endpoint for Home Assistant motion detection"""
        try:
            data = await request.json()
            logger.info(f"Motion webhook received: {data}")
            
            self.motion_detected = True
            self.motion_timestamp = datetime.now()
            
            # Get camera stream URL from data or use default
            self.camera_url = data.get('camera_url', '/api/camera-stream')
            
            return web.json_response({"status": "ok"})
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def poll_motion_sensor(self):
        """Poll Home Assistant motion sensor"""
        if not self.ha_token or not self.motion_sensor_entity_id:
            logger.warning("Missing HA token or motion sensor entity ID - polling disabled")
            return
        
        logger.info(f"Starting motion sensor polling for {self.motion_sensor_entity_id}")
        
        while True:
            try:
                async with ClientSession() as session:
                    headers = {"Authorization": f"Bearer {self.ha_token}"}
                    url = f"{self.ha_url}/api/states/{self.motion_sensor_entity_id}"
                    
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            current_state = data.get('state', 'off')
                            
                            # Log state changes
                            if self.last_motion_state != current_state:
                                logger.info(f"Motion state changed: {self.last_motion_state} -> {current_state}")
                            
                            # Check for state change from off to on
                            if self.last_motion_state == 'off' and current_state == 'on':
                                logger.info("Motion detected via polling!")
                                self.motion_detected = True
                                self.motion_timestamp = datetime.now()
                                self.camera_url = "/api/camera-stream"
                            elif self.last_motion_state == 'on' and current_state == 'off':
                                logger.info("Motion ended via polling - starting 5s cooldown")
                                self.motion_timestamp = datetime.now()  # Reset timestamp for cooldown
                            elif current_state == 'on':
                                # If still on, keep motion detected
                                self.motion_detected = True
                                if not self.motion_timestamp:
                                    self.motion_timestamp = datetime.now()
                                self.camera_url = "/api/camera-stream"
                            
                            self.last_motion_state = current_state
                        else:
                            logger.error(f"Failed to poll motion sensor: {resp.status}")
                            
            except Exception as e:
                logger.error(f"Motion polling error: {e}")
            
            # Poll every 0.5 seconds for responsive motion detection
            await asyncio.sleep(0.5)
    
    async def api_motion_check(self, request):
        """API endpoint to check for motion detection"""
        current_time = datetime.now()
        
        # Log current state for debugging
        logger.debug(f"Motion check - State: {self.last_motion_state}, Detected: {self.motion_detected}, Timestamp: {self.motion_timestamp}")
        
        # If motion is currently active, show camera
        if self.last_motion_state == 'on':
            return web.json_response({
                "motion_detected": True,
                "camera_url": self.camera_url or "/api/camera-stream",
                "timestamp": self.motion_timestamp.isoformat() if self.motion_timestamp else current_time.isoformat(),
                "reason": "motion_active"
            })
        
        # If motion recently turned off, show camera for 5 more seconds
        if (self.motion_detected and self.motion_timestamp and 
            current_time - self.motion_timestamp < timedelta(seconds=5)):
            
            seconds_left = 5 - (current_time - self.motion_timestamp).total_seconds()
            logger.debug(f"Motion cooldown - {seconds_left:.1f}s remaining")
            
            return web.json_response({
                "motion_detected": True,
                "camera_url": self.camera_url or "/api/camera-stream",
                "timestamp": self.motion_timestamp.isoformat(),
                "reason": "motion_cooldown",
                "cooldown_remaining": seconds_left
            })
        else:
            # Reset motion detection after cooldown
            if self.motion_detected and self.motion_timestamp:
                if current_time - self.motion_timestamp >= timedelta(seconds=5):
                    logger.info("Motion cooldown expired - clearing detection")
                    self.motion_detected = False
                    self.motion_timestamp = None
                    self.camera_url = None
            
            return web.json_response({
                "motion_detected": False
            })
    
    async def api_camera_stream(self, request):
        """Proxy camera stream from Home Assistant"""
        if not self.ha_token or not self.camera_entity_id:
            return web.Response(status=404, text="Camera not configured")
        
        try:
            async with ClientSession() as session:
                camera_url = f"{self.ha_url}/api/camera_proxy_stream/{self.camera_entity_id}"
                headers = {
                    "Authorization": f"Bearer {self.ha_token}"
                }
                
                async with session.get(camera_url, headers=headers) as resp:
                    if resp.status == 200:
                        # Stream the camera feed
                        response = web.StreamResponse(
                            status=200,
                            headers={
                                'Content-Type': resp.headers.get('Content-Type', 'image/jpeg')
                            }
                        )
                        await response.prepare(request)
                        
                        async for chunk in resp.content.iter_chunked(8192):
                            await response.write(chunk)
                        
                        return response
                    else:
                        logger.error(f"Camera stream error: {resp.status}")
                        return web.Response(status=resp.status)
                        
        except Exception as e:
            logger.error(f"Camera stream error: {e}")
            return web.Response(status=500, text=str(e))
    
    async def serve_static(self, request):
        """Serve static files"""
        filename = request.match_info.get('filename', 'index.html')
        
        if filename == '':
            filename = 'index.html'
        
        file_path = Path(__file__).parent / filename
        
        if not file_path.exists():
            return web.Response(status=404)
        
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
            
            content_type = 'text/html'
            if filename.endswith('.js'):
                content_type = 'application/javascript'
            elif filename.endswith('.css'):
                content_type = 'text/css'
            
            return web.Response(text=content, content_type=content_type)
        except Exception as e:
            logger.error(f"Error serving {filename}: {e}")
            return web.Response(status=500)

async def create_app():
    """Create the web application"""
    server = HomeDisplayServer()
    
    app = web.Application()
    
    # Start polling task after app is created
    async def start_polling(app):
        if server.ha_token and server.motion_sensor_entity_id:
            server._polling_task = asyncio.create_task(server.poll_motion_sensor())
            logger.info("Started motion sensor polling task")
        else:
            logger.warning(f"Cannot start polling - Token: {bool(server.ha_token)}, Sensor: {server.motion_sensor_entity_id}")
    
    app.on_startup.append(start_polling)
    
    # API routes
    app.router.add_post('/webhook/motion', server.webhook_motion)
    app.router.add_get('/api/motion-check', server.api_motion_check)
    app.router.add_get('/api/camera-stream', server.api_camera_stream)
    
    # Static file serving
    app.router.add_get('/', server.serve_static)
    app.router.add_get('/{filename}', server.serve_static)
    
    return app

if __name__ == '__main__':
    async def init():
        return await create_app()
    
    app = asyncio.run(init())
    web.run_app(app, host='0.0.0.0', port=8080)