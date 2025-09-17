import base64
import tempfile
import os
import logging
import warnings
import numpy as np
from PIL import Image

# Suppress pkg_resources deprecation warning from face_recognition_models
warnings.filterwarnings("ignore", message="pkg_resources is deprecated", category=UserWarning)

import face_recognition
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from facedetection.models import EmployeeFaceDetection
from employee.models import Employee
from attendance.models import Attendance, AttendanceActivity
from datetime import datetime, date
from django.utils import timezone

logger = logging.getLogger(__name__)


def encode_face_from_image(image_path):
    """
    Encode a face from an image file and return the face encoding
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        tuple: (success, encoding, message)
    """
    try:
        print(f"🔍 encode_face_from_image: Processing image at {image_path}")
        
        # Load the image
        image = face_recognition.load_image_file(image_path)
        print(f"🔍 Image loaded successfully, shape: {image.shape}")
        
        # Find face locations
        face_locations = face_recognition.face_locations(image)
        print(f"🔍 Found {len(face_locations)} face(s) in image")
        
        if not face_locations:
            return False, None, "No face detected in the image"
        
        if len(face_locations) > 1:
            return False, None, "Multiple faces detected. Please use an image with only one face"
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(image, face_locations)
        print(f"🔍 Generated {len(face_encodings)} face encoding(s)")
        
        if not face_encodings:
            return False, None, "Could not extract face encoding"
        
        # Convert to base64 string for storage
        encoding_str = base64.b64encode(face_encodings[0].tobytes()).decode('utf-8')
        
        return True, encoding_str, "Face encoding successful"
        
    except Exception as e:
        logger.error(f"Error encoding face: {str(e)}")
        return False, None, f"Error processing image: {str(e)}"


def compare_faces(known_encoding_str, unknown_encoding_str, tolerance=0.6):
    """
    Compare two face encodings and return similarity score
    
    Args:
        known_encoding_str (str): Base64 encoded known face
        unknown_encoding_str (str): Base64 encoded unknown face
        tolerance (float): Tolerance for face matching
        
    Returns:
        tuple: (match, distance, confidence)
    """
    try:
        # Decode the encodings
        known_encoding = np.frombuffer(base64.b64decode(known_encoding_str), dtype=np.float64)
        unknown_encoding = np.frombuffer(base64.b64decode(unknown_encoding_str), dtype=np.float64)
        
        # Calculate face distance
        face_distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
        
        # Calculate confidence (1 - distance, higher is better)
        confidence = max(0, 1 - face_distance)
        
        # Check if faces match based on tolerance
        match = face_distance <= tolerance
        
        return match, face_distance, confidence
        
    except Exception as e:
        logger.error(f"Error comparing faces: {str(e)}")
        return False, 1.0, 0.0


def process_uploaded_face_image(image_file):
    """
    Process uploaded face image and return encoding
    
    Args:
        image_file: Django uploaded file
        
    Returns:
        tuple: (success, encoding, message)
    """
    temp_file_path = None
    try:
        print(f"🔍 process_uploaded_face_image: Processing image file {image_file.name}, size: {image_file.size}")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file_path = temp_file.name
            # Save uploaded file to temporary location
            for chunk in image_file.chunks():
                temp_file.write(chunk)
            temp_file.flush()
        
        print(f"🔍 Saved image to temporary file: {temp_file_path}")
        
        # Process the image (outside the with block to ensure file is closed)
        success, encoding, message = encode_face_from_image(temp_file_path)
        
        print(f"🔍 Image encoding result: success={success}, message={message}")
        
        return success, encoding, message
            
    except Exception as e:
        logger.error(f"Error processing uploaded image: {str(e)}")
        return False, None, f"Error processing image: {str(e)}"
    finally:
        # Clean up temporary file in finally block
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except OSError as e:
                logger.warning(f"Could not delete temporary file {temp_file_path}: {e}")


def compare_uploaded_face_with_stored(employee_id, image_file, tolerance=0.6):
    """
    Compare uploaded face with stored face image for an employee
    
    Args:
        employee_id (int): Employee ID
        image_file: Uploaded image file
        tolerance (float): Face matching tolerance
        
    Returns:
        tuple: (match, confidence, message)
    """
    try:
        # Get the Employee instance first
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return False, 0.0, "Employee not found"
        
        # Get stored face image
        try:
            stored_face = EmployeeFaceDetection.objects.get(
                employee_id=employee
            )
            stored_image_path = stored_face.image.path
        except EmployeeFaceDetection.DoesNotExist:
            return False, 0.0, "No face registered for this employee"
        
        # Process uploaded image
        success, uploaded_encoding, message = process_uploaded_face_image(image_file)
        
        if not success:
            return False, 0.0, message
        
        # Process stored image
        success, stored_encoding, message = encode_face_from_image(stored_image_path)
        
        if not success:
            return False, 0.0, f"Error processing stored image: {message}"
        
        # Compare faces
        match, distance, confidence = compare_faces(
            stored_encoding, 
            uploaded_encoding, 
            tolerance
        )
        
        return match, confidence, "Face comparison completed"
        
    except Exception as e:
        logger.error(f"Error comparing uploaded face: {str(e)}")
        return False, 0.0, f"Error comparing faces: {str(e)}"


def find_employee_by_face(image_file, tolerance=0.6):
    """
    Find employee by face recognition from uploaded image
    
    Args:
        image_file: Uploaded image file
        tolerance (float): Face matching tolerance
        
    Returns:
        tuple: (employee, confidence, message)
    """
    try:
        print(f"🔍 find_employee_by_face: Processing image with tolerance {tolerance}")
        
        # Process uploaded image
        success, uploaded_encoding, message = process_uploaded_face_image(image_file)
        
        print(f"🔍 Image processing result: success={success}, message={message}")
        
        if not success:
            return None, 0.0, message
        
        # Get all face detection records
        all_faces = EmployeeFaceDetection.objects.all()
        print(f"🔍 Found {all_faces.count()} face detection records")
        
        best_match = None
        best_confidence = 0.0
        
        for face_data in all_faces:
            try:
                # Process stored image
                success, stored_encoding, message = encode_face_from_image(face_data.image.path)
                
                if success:
                    match, distance, confidence = compare_faces(
                        stored_encoding,
                        uploaded_encoding,
                        tolerance
                    )
                    
                    print(f"🔍 Comparing with employee {face_data.employee_id}: match={match}, confidence={confidence}")
                    
                    if match and confidence > best_confidence:
                        best_match = face_data.employee_id
                        best_confidence = confidence
                        print(f"🔍 New best match: employee {best_match} with confidence {best_confidence}")
            except Exception as e:
                logger.warning(f"Error processing face for employee {face_data.employee_id}: {e}")
                continue
        
        print(f"🔍 Final result: best_match={best_match}, best_confidence={best_confidence}")
        
        if best_match:
            return best_match, best_confidence, "Employee found"
        else:
            return None, 0.0, "No matching employee found"
            
    except Exception as e:
        logger.error(f"Error finding employee by face: {str(e)}")
        return None, 0.0, f"Error finding employee: {str(e)}"


def validate_face_image(image_file):
    """
    Validate if the uploaded image contains a valid face
    
    Args:
        image_file: Uploaded image file
        
    Returns:
        tuple: (valid, message)
    """
    try:
        # Process uploaded image
        success, encoding, message = process_uploaded_face_image(image_file)
        
        if not success:
            return False, message
        
        return True, "Valid face image"
        
    except Exception as e:
        logger.error(f"Error validating face image: {str(e)}")
        return False, f"Error validating image: {str(e)}"


def register_employee_face(employee_id, image_file):
    """
    Register face for an employee
    
    Args:
        employee_id (int): Employee ID
        image_file: Uploaded image file
        
    Returns:
        tuple: (success, message)
    """
    try:
        # Validate face image
        valid, message = validate_face_image(image_file)
        if not valid:
            return False, message
        
        # Get the Employee instance
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return False, "Employee not found"
        
        # Get or create employee face detection record
        # Since the model only has employee_id and image fields, we'll store the image directly
        face_detection, created = EmployeeFaceDetection.objects.get_or_create(
            employee_id=employee,
            defaults={
                'image': image_file
            }
        )
        
        if not created:
            # Update existing record with new image
            face_detection.image = image_file
            face_detection.save()
        
        return True, "Face registered successfully"
        
    except Exception as e:
        logger.error(f"Error registering employee face: {str(e)}")
        return False, f"Error registering face: {str(e)}"


def perform_face_attendance(employee_id, action, image_file, tolerance=0.6):
    """
    Perform attendance action using face recognition
    
    Args:
        employee_id (int): Employee ID
        action (str): 'checkin' or 'checkout'
        image_file: Uploaded image file
        tolerance (float): Face matching tolerance
        
    Returns:
        tuple: (success, attendance_data, message)
    """
    try:
        # Get employee first
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return False, None, "Employee not found"
        
        # Verify face
        match, confidence, message = compare_uploaded_face_with_stored(
            employee_id, image_file, tolerance
        )
        
        if not match:
            return False, None, f"Face verification failed: {message}"
        
        # Perform attendance action
        if action == 'checkin':
            return perform_clock_in(employee)
        elif action == 'checkout':
            return perform_clock_out(employee)
        else:
            return False, None, "Invalid action"
            
    except Exception as e:
        logger.error(f"Error performing face attendance: {str(e)}")
        return False, None, f"Error performing attendance: {str(e)}"


def perform_clock_in(employee):
    """
    Perform clock in for employee
    
    Args:
        employee: Employee instance
        
    Returns:
        tuple: (success, attendance_data, message)
    """
    try:
        # Get current time
        now = datetime.now()
        today = now.date()
        
        # Check if already clocked in today using consistent logic
        today_activities = AttendanceActivity.objects.filter(
            employee_id=employee, 
            attendance_date=today
        ).order_by("-id")
        
        is_already_checked_in = False
        if today_activities.exists():
            latest_activity = today_activities.first()
            # User is checked in if the latest activity doesn't have a clock_out_date
            is_already_checked_in = latest_activity and not latest_activity.clock_out_date
        
        if is_already_checked_in:
            # If already checked in, create a new attendance activity for additional check-in
            # This allows multiple check-ins per day while maintaining the main attendance record
            
            # Get or create the attendance record for today (handles unique constraint gracefully)
            attendance, created = Attendance.objects.get_or_create(
                employee_id=employee,
                attendance_date=today,
                defaults={
                    'attendance_clock_in_date': today,
                    'attendance_clock_in': now.time(),
                    'attendance_validated': True
                }
            )
            
            # Create additional attendance activity for this check-in
            AttendanceActivity.objects.create(
                employee_id=employee,
                attendance_date=today,
                clock_in_date=today,
                clock_in=now.time(),
                in_datetime=now,
                verification_method='face_recognition'
            )
            
            attendance_data = {
                'attendance_id': attendance.id,
                'clock_in_time': now,
                'employee_name': employee.get_full_name(),
                'employee_id': employee.id,
                'additional_checkin': not created  # True if this is an additional check-in
            }
            
            message = "Additional check-in recorded successfully" if not created else "Clock in successful"
            return True, attendance_data, message
        else:
            # Normal check-in for first time today
            attendance, created = Attendance.objects.get_or_create(
                employee_id=employee,
                attendance_date=today,
                defaults={
                    'attendance_clock_in_date': today,
                    'attendance_clock_in': now.time(),
                    'attendance_validated': True
                }
            )
            
            AttendanceActivity.objects.create(
                employee_id=employee,
                attendance_date=today,
                clock_in_date=today,
                clock_in=now.time(),
                in_datetime=now,
                verification_method='face_recognition'
            )
            
            attendance_data = {
                'attendance_id': attendance.id,
                'clock_in_time': now,
                'employee_name': employee.get_full_name(),
                'employee_id': employee.id
            }
            
            return True, attendance_data, "Clock in successful"
        
    except Exception as e:
        logger.error(f"Error performing clock in: {str(e)}")
        return False, None, f"Error clocking in: {str(e)}"


def perform_clock_out(employee):
    """
    Perform clock out for employee
    
    Args:
        employee: Employee instance
        
    Returns:
        tuple: (success, attendance_data, message)
    """
    try:
        print(f"🔍 perform_clock_out: Checking if employee {employee.id} is online")
        
        # Check if clocked in using the same logic as CheckingStatus API
        today = datetime.now().date()
        today_activities = AttendanceActivity.objects.filter(
            employee_id=employee, 
            attendance_date=today
        ).order_by("-id")
        
        is_online = False
        if today_activities.exists():
            latest_activity = today_activities.first()
            # User is checked in if the latest activity doesn't have a clock_out_date
            is_online = latest_activity and not latest_activity.clock_out_date
        
        print(f"🔍 Employee {employee.id} online status: {is_online}")
        
        if not is_online:
            return False, None, "Not clocked in"
        
        # Get current time
        now = datetime.now()
        today = now.date()
        
        # Get latest attendance
        attendance = Attendance.objects.filter(
            employee_id=employee,
            attendance_date=today
        ).order_by('-id').first()
        
        if not attendance:
            return False, None, "No attendance record found"
        
        # Update attendance
        attendance.attendance_clock_out_date = today
        attendance.attendance_clock_out = now.time()
        attendance.save()
        
        # Update attendance activity
        activity = AttendanceActivity.objects.filter(
            employee_id=employee,
            attendance_date=today,
            clock_out_date__isnull=True
        ).order_by('-id').first()
        
        if activity:
            activity.clock_out_date = today
            activity.clock_out = now.time()
            activity.out_datetime = now
            activity.verification_method = 'face_recognition'
            activity.save()
        
        attendance_data = {
            'attendance_id': attendance.id,
            'clock_out_time': now,
            'employee_name': employee.get_full_name(),
            'employee_id': employee.id
        }
        
        return True, attendance_data, "Clock out successful"
        
    except Exception as e:
        logger.error(f"Error performing clock out: {str(e)}")
        return False, None, f"Error clocking out: {str(e)}"


def get_face_recognition_stats(company_id=None):
    """
    Get face recognition statistics
    
    Args:
        company_id (int): Optional company ID filter
        
    Returns:
        dict: Statistics data
    """
    try:
        # Base queryset
        queryset = EmployeeFaceDetection.objects.all()
        
        if company_id:
            queryset = queryset.filter(employee_id_employee_work_info_company_id=company_id)
        
        total_registrations = queryset.count()
        active_registrations = total_registrations  # All registered faces are considered active
        
        # Get last recognition time (this would need to be tracked in a separate model)
        last_recognition_time = None
        
        stats = {
            'total_registrations': total_registrations,
            'active_registrations': active_registrations,
            'successful_recognitions': 0,  # Would need tracking
            'failed_recognitions': 0,  # Would need tracking
            'recognition_accuracy': 0.0,  # Would need tracking
            'last_recognition_time': last_recognition_time
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting face recognition stats: {str(e)}")
        return {
            'total_registrations': 0,
            'active_registrations': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'recognition_accuracy': 0.0,
            'last_recognition_time': None
        }