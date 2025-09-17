# Face Recognition API Documentation

This document provides comprehensive documentation for the Face Recognition API endpoints designed for mobile app integration.

## Base URL
```
/api/v1/facedetection/
```

## Authentication
All endpoints require authentication. Include the authentication token in the request headers:
```
Authorization: Bearer <your_token>
```

## API Endpoints

### 1. Face Detection Configuration

#### Get Configuration
```http
GET /api/v1/facedetection/config/
```
**Description:** Get face detection configuration for the user's company.

**Response:**
```json
{
    "id": 1,
    "company_id": 1,
    "company_name": "Your Company",
    "start": true,
    "threshold": 0.6,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Update Configuration
```http
POST /api/v1/facedetection/config/
```
**Description:** Update face detection configuration (Manager permission required).

**Request Body:**
```json
{
    "start": true,
    "threshold": 0.6
}
```

### 2. Employee Face Registration

#### Register Face
```http
POST /api/v1/facedetection/employees/
```
**Description:** Register face for an employee.

**Request Body (multipart/form-data):**
```
employee_id: 123
face_image: <image_file>
action: "register"
```

**Response:**
```json
{
    "success": true,
    "message": "Face registered successfully",
    "data": {
        "id": 1,
        "employee_id": 123,
        "employee_name": "John Doe",
        "employee_id_number": "EMP001",
        "company_name": "Your Company",
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
}
```

#### Get Employee Face Records
```http
GET /api/v1/facedetection/employees/
```
**Description:** Get all face detection records for the company.

**Query Parameters:**
- `page`: Page number for pagination
- `page_size`: Number of records per page

**Response:**
```json
{
    "count": 10,
    "next": "http://api.example.com/api/v1/facedetection/employees/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "employee_id": 123,
            "employee_name": "John Doe",
            "employee_id_number": "EMP001",
            "company_name": "Your Company",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

### 3. Face Verification and Attendance

#### Face Verification
```http
POST /api/v1/facedetection/verify/
```
**Description:** Verify face and perform attendance action.

**Request Body (multipart/form-data):**
```
face_image: <image_file>
employee_id: 123 (optional)
action: "checkin" | "checkout" | "verify"
```

**Response:**
```json
{
    "success": true,
    "message": "Clock in successful",
    "employee_id": 123,
    "employee_name": "John Doe",
    "confidence": 0.95,
    "action": "checkin",
    "attendance_data": {
        "attendance_id": 456,
        "clock_in_time": "2024-01-01T09:00:00Z",
        "employee_name": "John Doe",
        "employee_id": 123
    }
}
```

#### Quick Face Check-in
```http
POST /api/v1/facedetection/checkin/
```
**Description:** Quick face check-in for mobile apps.

**Request Body (multipart/form-data):**
```
face_image: <image_file>
```

**Response:**
```json
{
    "success": true,
    "message": "Clock in successful",
    "employee_id": 123,
    "employee_name": "John Doe",
    "confidence": 0.95,
    "attendance_data": {
        "attendance_id": 456,
        "clock_in_time": "2024-01-01T09:00:00Z",
        "employee_name": "John Doe",
        "employee_id": 123
    }
}
```

#### Quick Face Check-out
```http
POST /api/v1/facedetection/checkout/
```
**Description:** Quick face check-out for mobile apps.

**Request Body (multipart/form-data):**
```
face_image: <image_file>
```

**Response:**
```json
{
    "success": true,
    "message": "Clock out successful",
    "employee_id": 123,
    "employee_name": "John Doe",
    "confidence": 0.95,
    "attendance_data": {
        "attendance_id": 456,
        "clock_out_time": "2024-01-01T17:00:00Z",
        "employee_name": "John Doe",
        "employee_id": 123
    }
}
```

### 4. Face Image Validation

#### Validate Face Image
```http
POST /api/v1/facedetection/validate-image/
```
**Description:** Validate if uploaded image contains a valid face.

**Request Body (multipart/form-data):**
```
face_image: <image_file>
```

**Response:**
```json
{
    "valid": true,
    "message": "Valid face image"
}
```

### 5. Face Detection Status

#### Get Status
```http
GET /api/v1/facedetection/status/
```
**Description:** Get face detection status for the company.

**Response:**
```json
{
    "is_enabled": true,
    "company_id": 1,
    "company_name": "Your Company",
    "threshold": 0.6,
    "total_registered_faces": 10,
    "active_faces": 8
}
```

### 6. Statistics

#### Get Face Recognition Stats
```http
GET /api/v1/facedetection/stats/
```
**Description:** Get face recognition statistics.

**Response:**
```json
{
    "total_registrations": 10,
    "active_registrations": 8,
    "successful_recognitions": 150,
    "failed_recognitions": 5,
    "recognition_accuracy": 0.97,
    "last_recognition_time": "2024-01-01T17:00:00Z"
}
```

## Error Responses

### Common Error Codes

#### 400 Bad Request
```json
{
    "error": "Face image is required"
}
```

#### 401 Unauthorized
```json
{
    "error": "Authentication credentials were not provided"
}
```

#### 403 Forbidden
```json
{
    "error": "Permission denied"
}
```

#### 404 Not Found
```json
{
    "error": "Employee not found"
}
```

#### 500 Internal Server Error
```json
{
    "error": "Failed to process face recognition"
}
```

## Mobile App Integration Examples

### Android (Kotlin)
```kotlin
// Face registration
fun registerFace(employeeId: Int, imageFile: File) {
    val requestBody = MultipartBody.Builder()
        .setType(MultipartBody.FORM)
        .addFormDataPart("employee_id", employeeId.toString())
        .addFormDataPart("face_image", imageFile.name, 
            imageFile.asRequestBody("image/*".toMediaType()))
        .addFormDataPart("action", "register")
        .build()
    
    val request = Request.Builder()
        .url("$baseUrl/api/v1/facedetection/employees/")
        .post(requestBody)
        .addHeader("Authorization", "Bearer $token")
        .build()
    
    // Execute request
}
```

### iOS (Swift)
```swift
// Face check-in
func performFaceCheckin(image: UIImage) {
    let url = URL(string: "\(baseUrl)/api/v1/facedetection/checkin/")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    
    let boundary = "Boundary-\(UUID().uuidString)"
    request.setValue("multipart/form-data; boundary=\(boundary)", 
                    forHTTPHeaderField: "Content-Type")
    
    var body = Data()
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"face_image\"; filename=\"image.jpg\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
    body.append(image.jpegData(compressionQuality: 0.8)!)
    body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
    
    request.httpBody = body
    
    // Execute request
}
```

## Image Requirements

- **Format:** JPEG, JPG, or PNG
- **Size:** Maximum 5MB
- **Quality:** Clear, well-lit face
- **Content:** Single face per image
- **Resolution:** Minimum 200x200 pixels

## Security Considerations

1. **Authentication:** All endpoints require valid authentication tokens
2. **Permissions:** Some endpoints require manager-level permissions
3. **Data Privacy:** Face encodings are stored as base64-encoded strings
4. **Rate Limiting:** Consider implementing rate limiting for production use
5. **HTTPS:** Always use HTTPS in production environments

## Performance Tips

1. **Image Compression:** Compress images before sending to reduce upload time
2. **Caching:** Cache face detection configuration to reduce API calls
3. **Error Handling:** Implement proper error handling for network issues
4. **Offline Support:** Consider caching face data for offline verification

## Troubleshooting

### Common Issues

1. **"No face detected"**: Ensure the image contains a clear, single face
2. **"Face verification failed"**: Check if the employee has registered their face
3. **"Face detection not enabled"**: Contact administrator to enable face detection
4. **"Permission denied"**: Ensure user has required permissions

### Debug Mode

Enable debug logging by setting the log level to DEBUG in your Django settings:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'face_recognition.log',
        },
    },
    'loggers': {
        'horilla_api.api_methods.facedetection.face_recognition_utils': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Support

For technical support or questions about the Face Recognition API, please contact the development team or refer to the main project documentation.
