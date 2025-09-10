import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import PostureData, PostureSession, EmergencyAlert, UserProfile
from .ml_models import posture_analyzer
from .utils import send_emergency_call, send_vibration_signal
from datetime import datetime, timedelta
from django.utils import timezone

class PostureConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.device_id = None
        self.posture_history = []
        self.last_vibration_time = None
        
    async def connect(self):
        await self.accept()
        
    async def disconnect(self, close_code):
        if self.user:
            await self.update_device_connection_status(self.user.id, False)
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'device_connect':
                await self.handle_device_connection(data)
            elif message_type == 'posture_data':
                await self.handle_posture_data(data)
            elif message_type == 'heartbeat':
                await self.send(text_data=json.dumps({'type': 'heartbeat_ack'}))
                
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def handle_device_connection(self, data):
        device_id = data.get('device_id')
        user_id = data.get('user_id')
        
        try:
            self.user = await database_sync_to_async(User.objects.get)(id=user_id)
            self.device_id = device_id
            
            # Update device connection status
            await self.update_device_connection_status(user_id, True, device_id)
            
            await self.send(text_data=json.dumps({
                'type': 'connection_success',
                'message': 'Device connected successfully',
                'user': self.user.username
            }))
            
        except User.DoesNotExist:
            await self.send(text_data=json.dumps({
                'type': 'connection_error',
                'message': 'Invalid user'
            }))
    
    async def handle_posture_data(self, data):
        if not self.user:
            return
        
        sensor_data = data.get('sensor_data', {})
        tilt_x = sensor_data.get('tilt_x', 0)
        tilt_y = sensor_data.get('tilt_y', 0)
        gyro_x = sensor_data.get('gyro_x', 0)
        gyro_y = sensor_data.get('gyro_y', 0)
        gyro_z = sensor_data.get('gyro_z', 0)
        
        # Analyze posture and fall detection
        posture_result = posture_analyzer.predict_posture(tilt_x, tilt_y)
        fall_result = posture_analyzer.predict_fall(gyro_x, gyro_y, gyro_z)
        
        # Save to database
        posture_data = await self.save_posture_data(
            self.user.id, tilt_x, tilt_y, gyro_x, gyro_y, gyro_z,
            posture_result.get('is_correct') if posture_result else None,
            fall_result.get('is_fall') if fall_result else False
        )
        
        # Check for fall detection
        if fall_result and fall_result.get('is_fall'):
            await self.handle_fall_detection()
        
        # Check for posture correction
        if posture_result:
            await self.handle_posture_monitoring(posture_result.get('is_correct'))
        
        # Send real-time data to frontend
        await self.send(text_data=json.dumps({
            'type': 'posture_update',
            'data': {
                'timestamp': timezone.now().isoformat(),
                'tilt_x': tilt_x,
                'tilt_y': tilt_y,
                'gyro_x': gyro_x,
                'gyro_y': gyro_y,
                'gyro_z': gyro_z,
                'posture_correct': posture_result.get('is_correct') if posture_result else None,
                'posture_confidence': posture_result.get('confidence') if posture_result else None,
                'fall_detected': fall_result.get('is_fall') if fall_result else False,
                'fall_confidence': fall_result.get('confidence') if fall_result else None,
            }
        }))
    
    async def handle_fall_detection(self):
        # Create emergency alert
        await self.create_emergency_alert(self.user.id, 'fall')
        
        # Send emergency call
        emergency_contact = await self.get_emergency_contact(self.user.id)
        if emergency_contact:
            await database_sync_to_async(send_emergency_call)(emergency_contact, self.user.username)
        
        # Send alert to frontend
        await self.send(text_data=json.dumps({
            'type': 'fall_alert',
            'message': 'Fall detected! Emergency services contacted.',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def handle_posture_monitoring(self, is_correct_posture):
        # Add to posture history
        self.posture_history.append({
            'timestamp': timezone.now(),
            'is_correct': is_correct_posture
        })
        
        # Keep only last 5 minutes of data (300 seconds / 0.1 second intervals = 3000 samples)
        current_time = timezone.now()
        self.posture_history = [
            entry for entry in self.posture_history 
            if (current_time - entry['timestamp']).total_seconds() <= 300
        ]
        
        # Check if posture incorrectness is above 60% for 5 minutes
        if len(self.posture_history) >= 100:  # At least 10 seconds of data
            incorrect_count = sum(1 for entry in self.posture_history if not entry['is_correct'])
            incorrectness_percentage = (incorrect_count / len(self.posture_history)) * 100
            
            if incorrectness_percentage >= 60:
                # Check if 5 minutes have passed since last vibration
                if (not self.last_vibration_time or 
                    (current_time - self.last_vibration_time).total_seconds() >= 300):
                    
                    await self.send_vibration_alert()
                    self.last_vibration_time = current_time
    
    async def send_vibration_alert(self):
        # Send vibration signal to device
        await self.send(text_data=json.dumps({
            'type': 'vibration_command',
            'duration': 2000,  # 2 seconds
            'pattern': 'pulse'
        }))
        
        # Send alert to frontend
        await self.send(text_data=json.dumps({
            'type': 'posture_alert',
            'message': 'Poor posture detected. Vibration alert sent.',
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def save_posture_data(self, user_id, tilt_x, tilt_y, gyro_x, gyro_y, gyro_z, is_correct_posture, is_fall_detected):
        return PostureData.objects.create(
            user_id=user_id,
            tilt_x=tilt_x,
            tilt_y=tilt_y,
            gyro_x=gyro_x,
            gyro_y=gyro_y,
            gyro_z=gyro_z,
            is_correct_posture=is_correct_posture,
            is_fall_detected=is_fall_detected
        )
    
    @database_sync_to_async
    def update_device_connection_status(self, user_id, is_connected, device_id=None):
        profile, created = UserProfile.objects.get_or_create(user_id=user_id)
        profile.is_device_connected = is_connected
        if device_id:
            profile.device_id = device_id
        profile.save()
        return profile
    
    @database_sync_to_async
    def create_emergency_alert(self, user_id, alert_type):
        return EmergencyAlert.objects.create(
            user_id=user_id,
            alert_type=alert_type
        )
    
    @database_sync_to_async
    def get_emergency_contact(self, user_id):
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            return profile.emergency_contact
        except UserProfile.DoesNotExist:
            return None