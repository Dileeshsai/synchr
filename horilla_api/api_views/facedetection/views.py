import base64
import tempfile
import os
import logging
import warnings
from datetime import datetime, date
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

# Suppress pkg_resources deprecation warning from face_recognition_models
warnings.filterwarnings("ignore", message="pkg_resources is deprecated", category=UserWarning)

from facedetection.models import FaceDetection, EmployeeFaceDetection
from employee.models import Employee
from base.models import Company
from attendance.models import Attendance, AttendanceActivity

from ...api_serializers.facedetection.serializers import (
    FaceDetectionSerializer,
    EmployeeFaceDetectionSerializer,
    FaceRegistrationSerializer,
    FaceVerificationSerializer,
    FaceDetectionConfigSerializer,
    FaceRecognitionResponseSerializer,
    FaceDetectionStatusSerializer,
    FaceImageValidationSerializer,
    BulkFaceRegistrationSerializer,
    FaceRecognitionStatsSerializer
)

from ...api_methods.facedetection.face_recognition_utils import (
    encode_face_from_image,
    compare_faces,
    process_uploaded_face_image,
    compare_uploaded_face_with_stored,
    validate_face_image,
    find_employee_by_face,
    register_employee_face,
    perform_face_attendance,
    get_face_recognition_stats
)

from ...api_decorators.base.decorators import (
    manager_permission_required,
    permission_required,
)

logger = logging.getLogger(__name__)


class FaceDetectionConfigAPIView(APIView):
    """
    API View for managing face detection configuration
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get face detection configuration for the user's company"""
        try:
            # Check if user has an associated employee
            if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
                return Response(
                    {"error": "No employee profile found for this user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user.employee_get
            company = employee.get_company()
            
            if not company:
                return Response(
                    {"error": "No company found for this employee"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            face_detection, created = FaceDetection.objects.get_or_create(
                company_id=company,
                defaults={'start': False}
            )
            
            serializer = FaceDetectionSerializer(face_detection)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting face detection config: {str(e)}")
            return Response(
                {"error": "Failed to get face detection configuration"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @manager_permission_required("facedetection.change_facedetection")
    def post(self, request):
        """Update face detection configuration"""
        try:
            # Check if user has an associated employee
            if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
                return Response(
                    {"error": "No employee profile found for this user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user.employee_get
            company = employee.get_company()
            
            if not company:
                return Response(
                    {"error": "No company found for this employee"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = FaceDetectionConfigSerializer(data=request.data)
            if serializer.is_valid():
                face_detection, created = FaceDetection.objects.get_or_create(
                    company_id=company,
                    defaults={'start': False}
                )
                
                face_detection.start = serializer.validated_data['start']
                face_detection.save()
                
                response_serializer = FaceDetectionSerializer(face_detection)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error updating face detection config: {str(e)}")
            return Response(
                {"error": "Failed to update face detection configuration"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmployeeFaceDetectionGetPostAPIView(APIView):
    """
    API View for managing employee face detection records
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = PageNumberPagination
    
    def get(self, request):
        """Get face detection records for employees"""
        try:
            # Check if user has an associated employee
            if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
                return Response(
                    {"error": "No employee profile found for this user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user.employee_get
            company = employee.get_company()
            
            if not company:
                return Response(
                    {"error": "No company found for this employee"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get face detection records for the company
            face_records = EmployeeFaceDetection.objects.filter(
                employee_id_employee_work_info_company_id=company
            ).select_related('employee_id')
            
            # Apply pagination
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(face_records, request)
            
            serializer = EmployeeFaceDetectionSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error getting face detection records: {str(e)}")
            return Response(
                {"error": "Failed to get face detection records"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Register face for an employee"""
        try:
            # Check if user has an associated employee
            if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
                return Response(
                    {"error": "No employee profile found for this user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user.employee_get
            
            # Check if face image is provided
            if 'image' not in request.FILES:
                return Response(
                    {"error": "Face image is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            face_image = request.FILES['image']
            
            # Register face for the current user
            success, message = register_employee_face(employee.id, face_image)
            
            if success:
                # Get the created/updated record
                try:
                    face_record = EmployeeFaceDetection.objects.get(
                        employee_id=employee
                    )
                    response_serializer = EmployeeFaceDetectionSerializer(face_record)
                    
                    return Response({
                        "success": True,
                        "message": message,
                        "data": response_serializer.data
                    }, status=status.HTTP_201_CREATED)
                except EmployeeFaceDetection.DoesNotExist:
                    return Response({
                        "success": True,
                        "message": message
                    }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "success": False,
                    "message": message
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error registering face: {str(e)}")
            return Response(
                {"error": "Failed to register face"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FaceVerificationAPIView(APIView):
    """
    API View for face verification and attendance
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def post(self, request):
        """Verify face and perform attendance action"""
        try:
            # Check if face image is provided in files
            if 'face_image' not in request.FILES:
                return Response({
                    "face_image": ["No file was submitted."]
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Prepare data for serializer
            data = {
                'face_image': request.FILES['face_image'],
                'action': request.data.get('action', 'verify')
            }
            
            # Add employee_id if provided
            if 'employee_id' in request.data:
                data['employee_id'] = request.data['employee_id']
            
            serializer = FaceVerificationSerializer(data=data)
            if serializer.is_valid():
                face_image = serializer.validated_data['face_image']
                employee_id = serializer.validated_data.get('employee_id')
                action = serializer.validated_data['action']
                
                # Get face detection configuration
                if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
                    return Response(
                        {"error": "No employee profile found for this user"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                employee = request.user.employee_get
                company = employee.get_company()
                
                if not company:
                    return Response(
                        {"error": "No company found for this employee"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                try:
                    face_detection = FaceDetection.objects.get(company_id=company)
                    if not face_detection.start:
                        return Response({
                            "success": False,
                            "message": "Face detection is not enabled for your company"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    tolerance = 0.6  # Default threshold value
                except FaceDetection.DoesNotExist:
                    return Response({
                        "success": False,
                        "message": "Face detection is not configured for your company"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # If employee_id is provided, verify specific employee
                if employee_id:
                    match, confidence, message = compare_uploaded_face_with_stored(
                        employee_id, face_image, tolerance
                    )
                    
                    if match:
                        # Perform attendance action
                        success, attendance_data, msg = perform_face_attendance(
                            employee_id, action, face_image, tolerance
                        )
                        
                        if success:
                            return Response({
                                "success": True,
                                "message": msg,
                                "employee_id": employee_id,
                                "employee_name": Employee.objects.get(id=employee_id).get_full_name(),
                                "confidence": confidence,
                                "action": action,
                                "attendance_data": attendance_data
                            }, status=status.HTTP_200_OK)
                        else:
                            return Response({
                                "success": False,
                                "message": msg
                            }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({
                            "success": False,
                            "message": f"Face verification failed: {message}"
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # If no employee_id, find employee by face
                else:
                    found_employee, confidence, message = find_employee_by_face(
                        face_image, tolerance
                    )
                    
                    if found_employee:
                        # Perform attendance action
                        success, attendance_data, msg = perform_face_attendance(
                            found_employee.id, action, face_image, tolerance
                        )
                        
                        if success:
                            return Response({
                                "success": True,
                                "message": msg,
                                "employee_id": found_employee.id,
                                "employee_name": found_employee.get_full_name(),
                                "confidence": confidence,
                                "action": action,
                                "attendance_data": attendance_data
                            }, status=status.HTTP_200_OK)
                        else:
                            return Response({
                                "success": False,
                                "message": msg
                            }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({
                            "success": False,
                            "message": f"No matching employee found: {message}"
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error in face verification: {str(e)}")
            return Response(
                {"error": "Failed to verify face"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FaceImageValidationAPIView(APIView):
    """
    API View for validating face images
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Validate if uploaded image contains a valid face"""
        try:
            serializer = FaceImageValidationSerializer(data=request.data)
            if serializer.is_valid():
                face_image = serializer.validated_data['face_image']
                
                valid, message = validate_face_image(face_image)
                
                return Response({
                    "valid": valid,
                    "message": message
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error validating face image: {str(e)}")
            return Response(
                {"error": "Failed to validate face image"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FaceDetectionStatusAPIView(APIView):
    """
    API View for getting face detection status
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get face detection status for the user's company"""
        try:
            # Check if user has an associated employee
            if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
                return Response(
                    {"error": "No employee profile found for this user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user.employee_get
            company = employee.get_company()
            
            if not company:
                return Response(
                    {"error": "No company found for this employee"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get face detection configuration
            try:
                face_detection = FaceDetection.objects.get(company_id=company)
                is_enabled = face_detection.start
                threshold = 0.6  # Default threshold value
            except FaceDetection.DoesNotExist:
                is_enabled = False
                threshold = 0.6
            
            # Get face registration counts
            total_registered = EmployeeFaceDetection.objects.filter(
                employee_id_employee_work_info_company_id=company
            ).count()
            
            # Since EmployeeFaceDetection model doesn't have is_active field, 
            # we'll count all face records as active
            active_faces = EmployeeFaceDetection.objects.filter(
                employee_id_employee_work_info_company_id=company
            ).count()
            
            status_data = {
                "is_enabled": is_enabled,
                "company_id": company.id,
                "company_name": company.company,
                "threshold": threshold,
                "total_registered_faces": total_registered,
                "active_faces": active_faces
            }
            
            serializer = FaceDetectionStatusSerializer(status_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting face detection status: {str(e)}")
            return Response(
                {"error": "Failed to get face detection status"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkFaceRegistrationAPIView(APIView):
    """
    API View for bulk face registration
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @manager_permission_required("facedetection.add_employeefacedetection")
    def post(self, request):
        """Register faces for multiple employees"""
        try:
            # This would need to be implemented based on your specific requirements
            # For now, return a placeholder response
            return Response({
                "message": "Bulk face registration not yet implemented",
                "success": False
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
            
        except Exception as e:
            logger.error(f"Error in bulk face registration: {str(e)}")
            return Response(
                {"error": "Failed to perform bulk face registration"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FaceRecognitionStatsAPIView(APIView):
    """
    API View for getting face recognition statistics
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get face recognition statistics"""
        try:
            # Check if user has an associated employee
            if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
                return Response(
                    {"error": "No employee profile found for this user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user.employee_get
            company = employee.get_company()
            
            if not company:
                return Response(
                    {"error": "No company found for this employee"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            stats = get_face_recognition_stats(company.id)
            
            serializer = FaceRecognitionStatsSerializer(stats)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting face recognition stats: {str(e)}")
            return Response(
                {"error": "Failed to get face recognition statistics"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmployeeFaceDetectionDetailAPIView(APIView):
    """
    API View for individual employee face detection record operations
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Get specific employee face detection record"""
        try:
            face_record = get_object_or_404(EmployeeFaceDetection, pk=pk)
            
            # Check if user has permission to view this record
            if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
                return Response(
                    {"error": "No employee profile found for this user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user.employee_get
            company = employee.get_company()
            
            if not company:
                return Response(
                    {"error": "No company found for this employee"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if face_record.employee_id.employee_work_info.company_id != company:
                return Response(
                    {"error": "Permission denied"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = EmployeeFaceDetectionSerializer(face_record)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting face detection record: {str(e)}")
            return Response(
                {"error": "Failed to get face detection record"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @permission_required("facedetection.change_employeefacedetection")
    def put(self, request, pk):
        """Update employee face detection record"""
        try:
            face_record = get_object_or_404(EmployeeFaceDetection, pk=pk)
            
            # Check if user has permission to update this record
            if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
                return Response(
                    {"error": "No employee profile found for this user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user.employee_get
            company = employee.get_company()
            
            if not company:
                return Response(
                    {"error": "No company found for this employee"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if face_record.employee_id.employee_work_info.company_id != company:
                return Response(
                    {"error": "Permission denied"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = EmployeeFaceDetectionSerializer(
                face_record, data=request.data, partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error updating face detection record: {str(e)}")
            return Response(
                {"error": "Failed to update face detection record"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @permission_required("facedetection.delete_employeefacedetection")
    def delete(self, request, pk):
        """Delete employee face detection record"""
        try:
            face_record = get_object_or_404(EmployeeFaceDetection, pk=pk)
            
            # Check if user has permission to delete this record
            if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
                return Response(
                    {"error": "No employee profile found for this user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user.employee_get
            company = employee.get_company()
            
            if not company:
                return Response(
                    {"error": "No company found for this employee"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if face_record.employee_id.employee_work_info.company_id != company:
                return Response(
                    {"error": "Permission denied"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            face_record.delete()
            return Response(
                {"message": "Face detection record deleted successfully"}, 
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Exception as e:
            logger.error(f"Error deleting face detection record: {str(e)}")
            return Response(
                {"error": "Failed to delete face detection record"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def quick_face_checkin(request):
    """
    Quick face check-in endpoint for mobile apps
    """
    try:
        if 'face_image' not in request.FILES:
            return Response(
                {"error": "Face image is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        face_image = request.FILES['face_image']
        
        # Get face detection configuration
        if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
            return Response(
                {"error": "No employee profile found for this user"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        employee = request.user.employee_get
        company = employee.get_company()
        
        if not company:
            return Response(
                {"error": "No company found for this employee"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            face_detection = FaceDetection.objects.get(company_id=company)
            if not face_detection.start:
                return Response({
                    "success": False,
                    "message": "Face detection is not enabled for your company"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            tolerance = 0.6  # Default threshold value
        except FaceDetection.DoesNotExist:
            return Response({
                "success": False,
                "message": "Face detection is not configured for your company"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find employee by face
        found_employee, confidence, message = find_employee_by_face(
            face_image, tolerance
        )
        
        if found_employee:
            # Perform check-in
            success, attendance_data, msg = perform_face_attendance(
                found_employee.id, 'checkin', face_image, tolerance
            )
            
            if success:
                return Response({
                    "success": True,
                    "message": msg,
                    "employee_id": found_employee.id,
                    "employee_name": found_employee.get_full_name(),
                    "confidence": confidence,
                    "attendance_data": attendance_data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "success": False,
                    "message": msg
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                "success": False,
                "message": f"No matching employee found: {message}"
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in quick face checkin: {str(e)}")
        return Response(
            {"error": "Failed to perform face check-in"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def quick_face_checkout(request):
    """
    Quick face check-out endpoint for mobile apps
    """
    try:
        print(f"🔍 Face checkout request received from user: {request.user.username}")
        print(f"🔍 Request files: {list(request.FILES.keys())}")
        print(f"🔍 Request data: {request.data}")
        
        if 'face_image' not in request.FILES:
            print("❌ No face_image in request.FILES")
            return Response(
                {"error": "Face image is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        face_image = request.FILES['face_image']
        print(f"🔍 Face image received: {face_image.name}, size: {face_image.size}")
        
        # Get face detection configuration
        if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
            print("❌ No employee profile found for user")
            return Response(
                {"error": "No employee profile found for this user"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        employee = request.user.employee_get
        company = employee.get_company()
        
        if not company:
            print("❌ No company found for employee")
            return Response(
                {"error": "No company found for this employee"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f"🔍 Employee: {employee.get_full_name()}, Company: {company}")
        
        try:
            face_detection = FaceDetection.objects.get(company_id=company)
            if not face_detection.start:
                print("❌ Face detection not enabled for company")
                return Response({
                    "success": False,
                    "message": "Face detection is not enabled for your company"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            tolerance = 0.6  # Default threshold value
            print(f"🔍 Face detection enabled, tolerance: {tolerance}")
        except FaceDetection.DoesNotExist:
            print("❌ Face detection not configured for company")
            return Response({
                "success": False,
                "message": "Face detection is not configured for your company"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find employee by face
        print("🔍 Starting face recognition...")
        found_employee, confidence, message = find_employee_by_face(
            face_image, tolerance
        )
        
        print(f"🔍 Face recognition result: found_employee={found_employee}, confidence={confidence}, message={message}")
        
        if found_employee:
            # Perform check-out
            success, attendance_data, msg = perform_face_attendance(
                found_employee.id, 'checkout', face_image, tolerance
            )
            
            if success:
                return Response({
                    "success": True,
                    "message": msg,
                    "employee_id": found_employee.id,
                    "employee_name": found_employee.get_full_name(),
                    "confidence": confidence,
                    "attendance_data": attendance_data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "success": False,
                    "message": msg
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                "success": False,
                "message": f"No matching employee found: {message}"
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in quick face checkout: {str(e)}")
        return Response(
            {"error": "Failed to perform face check-out"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )