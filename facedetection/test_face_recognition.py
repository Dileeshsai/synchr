#!/usr/bin/env python3
"""
Test script for face recognition functionality
This script demonstrates how to use the face recognition utilities.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from facedetection.face_recognition_utils import (
    encode_face_from_image,
    compare_faces,
    validate_face_image,
    compare_uploaded_face_with_stored
)
from facedetection.models import EmployeeFaceDetection
from employee.models import Employee
from django.core.files.uploadedfile import SimpleUploadedFile

def test_face_encoding():
    """Test face encoding functionality."""
    print("=" * 60)
    print("TESTING FACE ENCODING")
    print("=" * 60)
    
    # Test with a sample image (you'll need to provide actual image paths)
    test_image_path = "path/to/test/image.jpg"  # Replace with actual path
    
    if os.path.exists(test_image_path):
        encoding, message = encode_face_from_image(test_image_path)
        if encoding is not None:
            print(f"✅ Face encoding successful: {message}")
            print(f"   Encoding shape: {encoding.shape}")
            print(f"   Encoding type: {type(encoding)}")
        else:
            print(f"❌ Face encoding failed: {message}")
    else:
        print(f"⚠️  Test image not found: {test_image_path}")
        print("   Please provide a valid image path to test face encoding")

def test_face_validation():
    """Test face validation functionality."""
    print("\n" + "=" * 60)
    print("TESTING FACE VALIDATION")
    print("=" * 60)
    
    test_image_path = "path/to/test/image.jpg"  # Replace with actual path
    
    if os.path.exists(test_image_path):
        result = validate_face_image(test_image_path)
        if result['valid']:
            print(f"✅ Face validation successful: {result['message']}")
            if 'face_size' in result:
                print(f"   Face size: {result['face_size']}")
        else:
            print(f"❌ Face validation failed: {result['message']}")
    else:
        print(f"⚠️  Test image not found: {test_image_path}")
        print("   Please provide a valid image path to test face validation")

def test_face_comparison():
    """Test face comparison functionality."""
    print("\n" + "=" * 60)
    print("TESTING FACE COMPARISON")
    print("=" * 60)
    
    reference_path = "path/to/reference/image.jpg"  # Replace with actual path
    new_image_path = "path/to/new/image.jpg"  # Replace with actual path
    
    if os.path.exists(reference_path) and os.path.exists(new_image_path):
        result = compare_faces(reference_path, new_image_path, tolerance=0.6)
        
        print(f"Success: {result['success']}")
        print(f"Face Matched: {result['face_matched']}")
        print(f"Message: {result['message']}")
        if result['distance'] is not None:
            print(f"Face Distance: {result['distance']:.4f}")
            print(f"Tolerance: {result['tolerance']}")
    else:
        print("⚠️  Test images not found:")
        print(f"   Reference: {reference_path}")
        print(f"   New image: {new_image_path}")
        print("   Please provide valid image paths to test face comparison")

def test_django_integration():
    """Test Django model integration."""
    print("\n" + "=" * 60)
    print("TESTING DJANGO INTEGRATION")
    print("=" * 60)
    
    try:
        # Get the first employee with face detection
        employee_face = EmployeeFaceDetection.objects.first()
        
        if employee_face:
            print(f"✅ Found employee face record:")
            print(f"   Employee: {employee_face.employee_id.employee_first_name} {employee_face.employee_id.employee_last_name}")
            print(f"   Face image: {employee_face.image.name}")
            print(f"   Image path: {employee_face.image.path}")
            
            # Test face encoding from stored image
            if os.path.exists(employee_face.image.path):
                encoding, message = encode_face_from_image(employee_face.image.path)
                if encoding is not None:
                    print(f"✅ Face encoding from stored image successful: {message}")
                else:
                    print(f"❌ Face encoding from stored image failed: {message}")
            else:
                print(f"⚠️  Stored image file not found: {employee_face.image.path}")
        else:
            print("⚠️  No employee face records found in database")
            print("   Please register some face images first")
            
    except Exception as e:
        print(f"❌ Django integration test failed: {str(e)}")

def main():
    """Run all tests."""
    print("HORILLA HRMS - FACE RECOGNITION TEST SUITE")
    print("=" * 60)
    
    # Test individual components
    test_face_encoding()
    test_face_validation()
    test_face_comparison()
    test_django_integration()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)
    print("\nTo run the standalone face recognition script:")
    print("python face_recognition_script.py <reference_image> <new_image> [tolerance]")
    print("\nExample:")
    print("python face_recognition_script.py reference.jpg new_photo.jpg 0.6")

if __name__ == "__main__":
    main()
