from rest_framework import serializers
from .models import ResultSession

class ResultSessionSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = ResultSession
        fields = [
            'id',
            'original_filename',
            'file_type',
            'file_size_bytes',
            'status',
            'error_message',
            'meta_info',
            'created_at',
            'expires_at',
            'is_expired',
        ]
        read_only_fields = fields

class SessionDetailSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = ResultSession
        fields = [
            'id',
            'original_filename',
            'file_type',
            'file_size_bytes',
            'status',
            'error_message',
            'meta_info',
            'parsed_dataset',
            'analytics_data',
            'created_at',
            'expires_at',
            'is_expired',
        ]
        read_only_fields = fields
