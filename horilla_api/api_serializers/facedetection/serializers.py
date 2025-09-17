from rest_framework import serializers
from facedetection.models import FaceDetection, EmployeeFaceDetection
from employee.models import Employee
from base.models import Company


class FaceDetectionSerializer(serializers.ModelSerializer):
    """
    Serializer for FaceDetection model configuration
    """
    company_name = serializers.CharField(source='company_id.company', read_only=True)
    
    class Meta:
        model = FaceDetection
        fields = [
            'id', 'company_id', 'company_name', 'start'
        ]
        read_only_fields = ['id']


class EmployeeFaceDetectionSerializer(serializers.ModelSerializer):
    """
    Serializer for EmployeeFaceDetection model
    """
    employee_name = serializers.CharField(source='employee_id.get_full_name', read_only=True)
    employee_id_number = serializers.CharField(source='employee_id.employee_id', read_only=True)
    company_name = serializers.CharField(source='employee_id.employee_work_info.company_id.company', read_only=True)
    
    class Meta:
        model = EmployeeFaceDetection
        fields = [
            'id', 'employee_id', 'employee_name', 'employee_id_number', 
            'company_name', 'image'
        ]
        read_only_fields = ['id']


class FaceRegistrationSerializer(serializers.Serializer):
    """
    Serializer for face registration process
    """
    employee_id = serializers.IntegerField()
    face_image = serializers.ImageField()
    action = serializers.ChoiceField(choices=['register', 'update', 'verify'])
    
    def validate_employee_id(self, value):
        try:
            employee = Employee.objects.get(id=value)
            if not employee.is_active:
                raise serializers.ValidationError("Employee is not active")
            return value
        except Employee.DoesNotExist:
            raise serializers.ValidationError("Employee does not exist")


class FaceVerificationSerializer(serializers.Serializer):
    """
    Serializer for face verification process
    """
    face_image = serializers.ImageField()
    employee_id = serializers.IntegerField(required=False)
    action = serializers.ChoiceField(choices=['checkin', 'checkout', 'verify'])
    
    def validate_face_image(self, value):
        # Basic validation for face image
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("Image size too large. Maximum 5MB allowed.")
        
        # Check file format
        allowed_formats = ['JPEG', 'JPG', 'PNG']
        try:
            if value.image.format not in allowed_formats:
                raise serializers.ValidationError(f"Unsupported image format. Allowed: {', '.join(allowed_formats)}")
        except Exception as e:
            raise serializers.ValidationError(f"Invalid image file: {str(e)}")
        
        return value
    
    def validate_employee_id(self, value):
        if value:
            try:
                employee = Employee.objects.get(id=value)
                if not employee.is_active:
                    raise serializers.ValidationError("Employee is not active")
                return value
            except Employee.DoesNotExist:
                raise serializers.ValidationError("Employee does not exist")
        return value


class FaceDetectionConfigSerializer(serializers.Serializer):
    """
    Serializer for face detection configuration
    """
    company_id = serializers.IntegerField()
    start = serializers.BooleanField()
    
    def validate_company_id(self, value):
        try:
            company = Company.objects.get(id=value)
            return value
        except Company.DoesNotExist:
            raise serializers.ValidationError("Company does not exist")


class FaceRecognitionResponseSerializer(serializers.Serializer):
    """
    Serializer for face recognition API responses
    """
    success = serializers.BooleanField()
    message = serializers.CharField()
    employee_id = serializers.IntegerField(required=False)
    employee_name = serializers.CharField(required=False)
    confidence = serializers.FloatField(required=False)
    action = serializers.CharField(required=False)
    attendance_id = serializers.IntegerField(required=False)
    clock_in_time = serializers.DateTimeField(required=False)
    clock_out_time = serializers.DateTimeField(required=False)


class FaceDetectionStatusSerializer(serializers.Serializer):
    """
    Serializer for face detection status check
    """
    is_enabled = serializers.BooleanField()
    company_id = serializers.IntegerField()
    company_name = serializers.CharField()
    threshold = serializers.FloatField()
    total_registered_faces = serializers.IntegerField()
    active_faces = serializers.IntegerField()


class FaceImageValidationSerializer(serializers.Serializer):
    """
    Serializer for face image validation
    """
    face_image = serializers.ImageField()
    
    def validate_face_image(self, value):
        # Basic validation for face image
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("Image size too large. Maximum 5MB allowed.")
        
        # Check file format
        allowed_formats = ['JPEG', 'JPG', 'PNG']
        try:
            if value.image.format not in allowed_formats:
                raise serializers.ValidationError(f"Unsupported image format. Allowed: {', '.join(allowed_formats)}")
        except Exception as e:
            raise serializers.ValidationError(f"Invalid image file: {str(e)}")
        
        return value


class BulkFaceRegistrationSerializer(serializers.Serializer):
    """
    Serializer for bulk face registration
    """
    employee_faces = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )
    
    def validate_employee_faces(self, value):
        for face_data in value:
            if 'employee_id' not in face_data or 'face_image' not in face_data:
                raise serializers.ValidationError("Each face data must contain employee_id and face_image")
        return value


class FaceRecognitionStatsSerializer(serializers.Serializer):
    """
    Serializer for face recognition statistics
    """
    total_registrations = serializers.IntegerField()
    active_registrations = serializers.IntegerField()
    successful_recognitions = serializers.IntegerField()
    failed_recognitions = serializers.IntegerField()
    recognition_accuracy = serializers.FloatField()
    last_recognition_time = serializers.DateTimeField(required=False)
