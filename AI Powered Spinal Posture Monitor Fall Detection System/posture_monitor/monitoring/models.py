from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    emergency_contact = models.CharField(max_length=15, blank=True)
    device_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    is_device_connected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class PostureData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    tilt_x = models.FloatField()
    tilt_y = models.FloatField()
    gyro_x = models.FloatField()
    gyro_y = models.FloatField()
    gyro_z = models.FloatField()
    is_correct_posture = models.BooleanField(null=True, blank=True)
    is_fall_detected = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']

class PostureSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    total_correct_posture_time = models.DurationField(null=True, blank=True)
    total_incorrect_posture_time = models.DurationField(null=True, blank=True)
    posture_correctness_percentage = models.FloatField(null=True, blank=True)
    vibration_alerts = models.IntegerField(default=0)
    fall_alerts = models.IntegerField(default=0)

class EmergencyAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=[
        ('fall', 'Fall Detected'),
        ('posture', 'Poor Posture Alert')
    ])
    timestamp = models.DateTimeField(default=timezone.now)
    is_resolved = models.BooleanField(default=False)
    emergency_contact_notified = models.BooleanField(default=False)