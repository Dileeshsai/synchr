"""
Face Recognition Utilities for Horilla HRMS
This module provides utility functions for face recognition operations.
"""

import os
import tempfile
import face_recognition
from PIL import Image
import numpy as np
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)

def encode_face_from_image(image_path):
    """
    Encode a face from an image file.
    
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
            return None, "No face detected in the image"
        
        if len(face_locations) > 1:
            logger.warning(f"Multiple faces detected in image. Using the first face.")
        
        # Encode the face
        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        if not face_encodings:
            return None, "Could not encode face from the image"
        
        return face_encodings[0], "Face encoded successfully"
        
    except Exception as e:
        logger.error(f"Error encoding face from {image_path}: {str(e)}")
        return None, f"Error processing image: {str(e)}"

def compare_faces(reference_encoding, new_image_path, tolerance=0.6):
    """
    Compare a face encoding with a new image.
    
    Args:
        reference_encoding (numpy.array): Face encoding from reference image
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
    
    try:
        # Encode face from new image
        new_encoding, encode_message = encode_face_from_image(new_image_path)
        
        if new_encoding is None:
            result['message'] = f"Could not process new image: {encode_message}"
            return result
        
        # Calculate face distance
        face_distance = face_recognition.face_distance([reference_encoding], new_encoding)[0]
        result['distance'] = float(face_distance)
        
        # Check if faces match based on tolerance
        if face_distance <= tolerance:
            result['success'] = True
            result['face_matched'] = True
            result['message'] = f"Face matched successfully (Distance: {face_distance:.4f})"
            logger.info(f"Face recognition successful: {result['message']}")
        else:
            result['success'] = True
            result['face_matched'] = False
            result['message'] = f"Face not matched (Distance: {face_distance:.4f}, Tolerance: {tolerance})"
            logger.info(f"Face recognition failed: {result['message']}")
            
    except Exception as e:
        result['message'] = f"Error during face comparison: {str(e)}"
        logger.error(f"Face comparison error: {str(e)}")
    
    return result

def process_uploaded_face_image(uploaded_file):
    """
    Process an uploaded face image and return the face encoding.
    
    Args:
        uploaded_file: Django uploaded file object
        
    Returns:
        tuple: (face_encoding, success_message)
    """
    try:
        # Create a temporary file to save the uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        # Encode the face
        face_encoding, message = encode_face_from_image(temp_file_path)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        return face_encoding, message
        
    except Exception as e:
        logger.error(f"Error processing uploaded face image: {str(e)}")
        return None, f"Error processing uploaded image: {str(e)}"

def compare_uploaded_face_with_stored(reference_image_path, uploaded_file, tolerance=0.6):
    """
    Compare an uploaded face image with a stored reference image.
    
    Args:
        reference_image_path (str): Path to the stored reference image
        uploaded_file: Django uploaded file object
        tolerance (float): Face matching tolerance
        
    Returns:
        dict: Result dictionary with comparison results
    """
    try:
        # Get reference face encoding
        reference_encoding, ref_message = encode_face_from_image(reference_image_path)
        
        if reference_encoding is None:
            return {
                'success': False,
                'message': f"Reference image error: {ref_message}",
                'face_matched': False
            }
        
        # Process uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        # Compare faces
        result = compare_faces(reference_encoding, temp_file_path, tolerance)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in face comparison: {str(e)}")
        return {
            'success': False,
            'message': f"Error during face comparison: {str(e)}",
            'face_matched': False
        }

def validate_face_image(image_path, min_face_size=50):
    """
    Validate that an image contains a detectable face.
    
    Args:
        image_path (str): Path to the image file
        min_face_size (int): Minimum face size in pixels
        
    Returns:
        dict: Validation result with success status and message
    """
    try:
        # Load the image
        image = face_recognition.load_image_file(image_path)
        
        # Find face locations
        face_locations = face_recognition.face_locations(image)
        
        if not face_locations:
            return {
                'valid': False,
                'message': 'No face detected in the image'
            }
        
        if len(face_locations) > 1:
            return {
                'valid': False,
                'message': 'Multiple faces detected. Please upload an image with only one face.'
            }
        
        # Check face size
        top, right, bottom, left = face_locations[0]
        face_width = right - left
        face_height = bottom - top
        
        if face_width < min_face_size or face_height < min_face_size:
            return {
                'valid': False,
                'message': f'Face is too small. Minimum size required: {min_face_size}x{min_face_size} pixels'
            }
        
        return {
            'valid': True,
            'message': 'Face validation successful',
            'face_size': (face_width, face_height)
        }
        
    except Exception as e:
        logger.error(f"Error validating face image: {str(e)}")
        return {
            'valid': False,
            'message': f'Error validating image: {str(e)}'
        }
