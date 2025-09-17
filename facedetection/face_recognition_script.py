#!/usr/bin/env python3
"""
Face Recognition Script for Horilla HRMS
This script compares a newly uploaded photo against a previously stored reference photo
using the face_recognition library.
"""

import os
import sys
import face_recognition
from PIL import Image
import numpy as np

def load_and_encode_face(image_path):
    """
    Load an image and encode the face in it.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        tuple: (face_encoding, success_message)
        - face_encoding: numpy array of face encoding or None
        - success_message: string message indicating success or error
    """
    try:
        # Load the image
        image = face_recognition.load_image_file(image_path)
        
        # Find face locations in the image
        face_locations = face_recognition.face_locations(image)
        
        if not face_locations:
            return None, f"Error: No face detected in {os.path.basename(image_path)}"
        
        if len(face_locations) > 1:
            return None, f"Warning: Multiple faces detected in {os.path.basename(image_path)}. Using the first face."
        
        # Encode the face
        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        if not face_encodings:
            return None, f"Error: Could not encode face in {os.path.basename(image_path)}"
        
        return face_encodings[0], f"Success: Face encoded from {os.path.basename(image_path)}"
        
    except FileNotFoundError:
        return None, f"Error: Image file not found: {image_path}"
    except Exception as e:
        return None, f"Error processing {os.path.basename(image_path)}: {str(e)}"

def compare_faces(reference_image_path, new_image_path, tolerance=0.6):
    """
    Compare faces between a reference image and a new image.
    
    Args:
        reference_image_path (str): Path to the reference image
        new_image_path (str): Path to the new image to compare
        tolerance (float): Face matching tolerance (lower = more strict)
        
    Returns:
        dict: Result dictionary with success status, message, and match details
    """
    result = {
        'success': False,
        'message': '',
        'face_matched': False,
        'distance': None,
        'tolerance': tolerance
    }
    
    # Load and encode reference face
    print(f"Loading reference image: {reference_image_path}")
    reference_encoding, ref_message = load_and_encode_face(reference_image_path)
    print(ref_message)
    
    if reference_encoding is None:
        result['message'] = f"Reference image error: {ref_message}"
        return result
    
    # Load and encode new face
    print(f"Loading new image: {new_image_path}")
    new_encoding, new_message = load_and_encode_face(new_image_path)
    print(new_message)
    
    if new_encoding is None:
        result['message'] = f"New image error: {new_message}"
        return result
    
    # Compare faces
    try:
        # Calculate face distance
        face_distance = face_recognition.face_distance([reference_encoding], new_encoding)[0]
        result['distance'] = float(face_distance)
        
        # Check if faces match based on tolerance
        if face_distance <= tolerance:
            result['success'] = True
            result['face_matched'] = True
            result['message'] = f"Success: Face Matched (Distance: {face_distance:.4f}, Tolerance: {tolerance})"
            print(f"✅ {result['message']}")
        else:
            result['success'] = True
            result['face_matched'] = False
            result['message'] = f"Error: Face Not Matched (Distance: {face_distance:.4f}, Tolerance: {tolerance})"
            print(f"❌ {result['message']}")
            
    except Exception as e:
        result['message'] = f"Error during face comparison: {str(e)}"
        print(f"❌ {result['message']}")
    
    return result

def main():
    """
    Main function to run face comparison from command line.
    Usage: python face_recognition_script.py <reference_image> <new_image> [tolerance]
    """
    if len(sys.argv) < 3:
        print("Usage: python face_recognition_script.py <reference_image> <new_image> [tolerance]")
        print("Example: python face_recognition_script.py reference.jpg new_photo.jpg 0.6")
        sys.exit(1)
    
    reference_path = sys.argv[1]
    new_image_path = sys.argv[2]
    tolerance = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
    
    # Validate file paths
    if not os.path.exists(reference_path):
        print(f"Error: Reference image not found: {reference_path}")
        sys.exit(1)
    
    if not os.path.exists(new_image_path):
        print(f"Error: New image not found: {new_image_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("HORILLA HRMS - FACE RECOGNITION SYSTEM")
    print("=" * 60)
    print(f"Reference Image: {reference_path}")
    print(f"New Image: {new_image_path}")
    print(f"Tolerance: {tolerance}")
    print("-" * 60)
    
    # Perform face comparison
    result = compare_faces(reference_path, new_image_path, tolerance)
    
    print("-" * 60)
    print("FINAL RESULT:")
    print(f"Success: {result['success']}")
    print(f"Face Matched: {result['face_matched']}")
    print(f"Message: {result['message']}")
    if result['distance'] is not None:
        print(f"Face Distance: {result['distance']:.4f}")
    print("=" * 60)
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] and result['face_matched'] else 1)

if __name__ == "__main__":
    main()
