"""
Django management command to test face recognition functionality
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from employee.models import Employee
from facedetection.models import EmployeeFaceDetection, FaceDetection
from facedetection.face_recognition_utils import (
    encode_face_from_image,
    validate_face_image,
    compare_faces
)
import os

class Command(BaseCommand):
    help = 'Test face recognition functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--employee-id',
            type=int,
            help='Employee ID to test face recognition for',
        )
        parser.add_argument(
            '--test-image',
            type=str,
            help='Path to test image for comparison',
        )
        parser.add_argument(
            '--tolerance',
            type=float,
            default=0.6,
            help='Face matching tolerance (default: 0.6)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('HORILLA HRMS - FACE RECOGNITION TEST')
        )
        self.stdout.write('=' * 50)
        
        # Test 1: Check face detection configuration
        self.test_face_detection_config()
        
        # Test 2: Check employee face registrations
        self.test_employee_face_registrations()
        
        # Test 3: Test face recognition if employee ID provided
        if options.get('employee_id'):
            self.test_employee_face_recognition(
                options['employee_id'],
                options.get('test_image'),
                options.get('tolerance', 0.6)
            )
        
        # Test 4: Test face validation if test image provided
        if options.get('test_image'):
            self.test_face_validation(options['test_image'])

    def test_face_detection_config(self):
        """Test face detection configuration."""
        self.stdout.write('\n1. Testing Face Detection Configuration:')
        self.stdout.write('-' * 40)
        
        face_detections = FaceDetection.objects.all()
        
        if face_detections.exists():
            for fd in face_detections:
                company_name = fd.company_id.company if fd.company_id else "Global"
                status = "Enabled" if fd.start else "Disabled"
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {company_name}: Face Detection {status}')
                )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  No face detection configurations found')
            )

    def test_employee_face_registrations(self):
        """Test employee face registrations."""
        self.stdout.write('\n2. Testing Employee Face Registrations:')
        self.stdout.write('-' * 40)
        
        employee_faces = EmployeeFaceDetection.objects.all()
        
        if employee_faces.exists():
            for ef in employee_faces:
                employee_name = f"{ef.employee_id.employee_first_name} {ef.employee_id.employee_last_name}"
                badge_id = ef.employee_id.badge_id
                
                # Check if image file exists
                image_exists = os.path.exists(ef.image.path) if ef.image else False
                status = "✅" if image_exists else "❌"
                
                self.stdout.write(
                    f'{status} {employee_name} ({badge_id}): {ef.image.name}'
                )
                
                if image_exists:
                    # Test face encoding
                    try:
                        encoding, message = encode_face_from_image(ef.image.path)
                        if encoding is not None:
                            self.stdout.write(
                                f'   ✅ Face encoding successful: {message}'
                            )
                        else:
                            self.stdout.write(
                                self.style.ERROR(f'   ❌ Face encoding failed: {message}')
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'   ❌ Error encoding face: {str(e)}')
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Image file not found: {ef.image.path}')
                    )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  No employee face registrations found')
            )

    def test_employee_face_recognition(self, employee_id, test_image_path, tolerance):
        """Test face recognition for a specific employee."""
        self.stdout.write(f'\n3. Testing Face Recognition for Employee ID {employee_id}:')
        self.stdout.write('-' * 40)
        
        try:
            employee = Employee.objects.get(id=employee_id)
            self.stdout.write(f'Employee: {employee.employee_first_name} {employee.employee_last_name}')
            
            # Get employee face record
            try:
                employee_face = EmployeeFaceDetection.objects.get(employee_id=employee)
                self.stdout.write(f'Face image: {employee_face.image.name}')
                
                if not os.path.exists(employee_face.image.path):
                    self.stdout.write(
                        self.style.ERROR('❌ Stored face image not found')
                    )
                    return
                
                if not test_image_path or not os.path.exists(test_image_path):
                    self.stdout.write(
                        self.style.WARNING('⚠️  Test image not provided or not found')
                    )
                    return
                
                # Perform face comparison
                self.stdout.write(f'Comparing with: {test_image_path}')
                self.stdout.write(f'Tolerance: {tolerance}')
                
                result = compare_faces(
                    employee_face.image.path,
                    test_image_path,
                    tolerance
                )
                
                if result['success']:
                    if result['face_matched']:
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ {result["message"]}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'❌ {result["message"]}')
                        )
                    
                    if result['distance'] is not None:
                        self.stdout.write(f'Face Distance: {result["distance"]:.4f}')
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {result["message"]}')
                    )
                    
            except EmployeeFaceDetection.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING('⚠️  No face registration found for this employee')
                )
                
        except Employee.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Employee with ID {employee_id} not found')
            )

    def test_face_validation(self, test_image_path):
        """Test face validation for a test image."""
        self.stdout.write(f'\n4. Testing Face Validation:')
        self.stdout.write('-' * 40)
        self.stdout.write(f'Test image: {test_image_path}')
        
        if not os.path.exists(test_image_path):
            self.stdout.write(
                self.style.ERROR('❌ Test image not found')
            )
            return
        
        result = validate_face_image(test_image_path)
        
        if result['valid']:
            self.stdout.write(
                self.style.SUCCESS(f'✅ {result["message"]}')
            )
            if 'face_size' in result:
                self.stdout.write(f'Face size: {result["face_size"]}')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ {result["message"]}')
            )
