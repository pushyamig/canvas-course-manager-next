from typing import List

from django.contrib.auth.models import User
from rest_framework import fields, serializers


class GlobalsUserSerializer(serializers.ModelSerializer):
    """
    Basic serializer for User model for sharing basic attributes with the UI as globals
    """

    class Meta:
        model = User
        fields = ['loginId', 'isStaff']  # Change is_staff to isStaff
    
    loginId = serializers.CharField(source='username')
    isStaff = serializers.BooleanField(source='is_staff')  # Add isStaff field