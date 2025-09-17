# Face Recognition System for Horilla HRMS

This module provides face recognition functionality for attendance tracking in the Horilla HRMS system.

## Features

- **Face Registration**: Employees can register their face images for attendance tracking
- **Face Recognition Attendance**: Clock in/out using face recognition
- **Face Validation**: Automatic validation of uploaded face images
- **Real-time Processing**: Live camera capture and face comparison
- **Admin Configuration**: Company-wide face detection settings

## Installation

### 1. Install Required Dependencies

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev libboost-python-dev

# Install Python dependencies
pip install -r facedetection/requirements_face_recognition.txt
```

### 2. Alternative Installation (if above fails)

```bash
# Install cmake first
pip install cmake

# Install dlib (this may take a while)
pip install dlib

# Install face_recognition
pip install face_recognition

# Install other dependencies
pip install opencv-python numpy Pillow scikit-image
```

### 3. Verify Installation

```bash
# Test the face recognition script
python facedetection/face_recognition_script.py --help

# Run Django tests
python manage.py test_face_recognition
```

## Usage

### 1. Admin Setup

1. **Enable Face Detection**:
   - Login as admin/HR manager
   - Go to Face Detection configuration
   - Enable face detection for your company

### 2. Employee Face Registration

1. **Employee Registration**:
   - Login as employee
   - Go to Profile → Face Registration tab
   - Upload a clear face image
   - System validates the image contains a detectable face

### 3. Face Recognition Attendance

1. **Using Face Recognition**:
   - Go to attendance area
   - Click "Face Recognition" button
   - Allow camera access
   - Position face in camera view
   - Click "Capture & Recognize"
   - System compares captured image with registered face

## API Endpoints

### Face Registration
- `POST /api/facedetection/employee-registration/` - Upload face image
- `DELETE /api/facedetection/employee-delete/` - Delete face image

### Face Recognition Attendance
- `GET /api/facedetection/attendance-interface/` - Face recognition interface
- `POST /api/facedetection/attendance-clock-in/` - Face recognition clock in
- `POST /api/facedetection/attendance-clock-out/` - Face recognition clock out

## Configuration

### Face Recognition Tolerance

The face recognition tolerance can be adjusted in the views:

```python
# In facedetection/views.py
recognition_result = compare_uploaded_face_with_stored(
    stored_face_path, 
    captured_image, 
    tolerance=0.6  # Adjust this value (0.0 = strict, 1.0 = lenient)
)
```

**Tolerance Guidelines**:
- `0.4-0.5`: Very strict (high security, may reject valid faces)
- `0.6`: Balanced (recommended default)
- `0.7-0.8`: Lenient (may accept similar faces)

### Face Validation Settings

```python
# In facedetection/face_recognition_utils.py
def validate_face_image(image_path, min_face_size=50):
    # Adjust min_face_size for minimum face size requirement
```

## Testing

### 1. Standalone Script Testing

```bash
# Test face comparison between two images
python facedetection/face_recognition_script.py reference.jpg test_image.jpg 0.6
```

### 2. Django Management Command

```bash
# Test face recognition system
python manage.py test_face_recognition

# Test specific employee
python manage.py test_face_recognition --employee-id 1 --test-image path/to/test.jpg

# Test with custom tolerance
python manage.py test_face_recognition --employee-id 1 --test-image path/to/test.jpg --tolerance 0.5
```

### 3. Python Test Script

```bash
# Run comprehensive tests
python facedetection/test_face_recognition.py
```

## Troubleshooting

### Common Issues

1. **"No face detected" Error**:
   - Ensure the image contains a clear, front-facing face
   - Check image quality and lighting
   - Verify the face is not too small or too large

2. **"Multiple faces detected" Error**:
   - Upload an image with only one person's face
   - Crop the image to focus on one face

3. **Camera Access Issues**:
   - Ensure browser has camera permissions
   - Use HTTPS for camera access
   - Check if camera is being used by another application

4. **Installation Issues**:
   - Install system dependencies first
   - Use virtual environment
   - Try installing dlib separately before face_recognition

### Performance Optimization

1. **Image Size**: Keep uploaded images under 1MB for faster processing
2. **Face Size**: Ensure faces are at least 50x50 pixels
3. **Image Format**: Use JPG format for better compression
4. **Tolerance**: Adjust tolerance based on your security requirements

## Security Considerations

1. **Data Privacy**: Face images are stored securely and only used for attendance
2. **Access Control**: Only authenticated employees can access face recognition
3. **Company Isolation**: Face detection is company-specific
4. **Image Validation**: All uploaded images are validated for face presence

## File Structure

```
facedetection/
├── models.py                          # Database models
├── views.py                           # Django views
├── urls.py                            # URL routing
├── face_recognition_script.py         # Standalone face recognition script
├── face_recognition_utils.py          # Face recognition utilities
├── test_face_recognition.py           # Test script
├── requirements_face_recognition.txt  # Dependencies
├── management/commands/
│   └── test_face_recognition.py       # Django management command
└── templates/facedetection/
    ├── face_attendance_interface.html # Main face recognition interface
    ├── face_attendance_disabled.html  # Error template
    ├── face_attendance_not_registered.html
    └── face_attendance_error.html
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the test scripts for examples
3. Check Django logs for error messages
4. Verify all dependencies are properly installed

## License

This face recognition module is part of the Horilla HRMS system and follows the same licensing terms.
