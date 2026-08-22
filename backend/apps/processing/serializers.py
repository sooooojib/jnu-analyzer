from rest_framework import serializers

class ProcessRequestSerializer(serializers.Serializer):
    reprocess = serializers.BooleanField(default=False, required=False)

class StudentLookupSerializer(serializers.Serializer):
    student_id = serializers.CharField(max_length=64, required=True)

class CompareRequestSerializer(serializers.Serializer):
    student_a = serializers.CharField(max_length=64, required=True)
    student_b = serializers.CharField(max_length=64, required=True)
