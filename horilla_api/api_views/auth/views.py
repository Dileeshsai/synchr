from django.contrib.auth import authenticate, get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail

from ...api_serializers.auth.serializers import GetEmployeeSerializer, ForgotPasswordSerializer
from employee.models import Employee



class LoginAPIView(APIView):
    def post(self, request):
        if "username" in request.data.keys() and "password" in request.data.keys():
            username = request.data.get("username")
            password = request.data.get("password")
            user = authenticate(username=username, password=password)
            if user:
                refresh = RefreshToken.for_user(user)
                employee = user.employee_get
                face_detection = False
                face_detection_image = None
                geo_fencing = False
                company_id = None  # <-- Fix: Initialize company_id
                try:
                    face_detection = employee.get_company().face_detection.start
                except:
                    pass
                try:
                    geo_fencing = employee.get_company().geo_fencing.start
                except:
                    pass
                try:
                    face_detection_image = employee.face_detection.image.url
                except:
                    pass
                try:
                    company_id = employee.get_company().id
                except:
                    pass
                result = {
                    "employee": GetEmployeeSerializer(employee).data,
                    "access": str(refresh.access_token),
                    "face_detection": face_detection,
                    "face_detection_image": face_detection_image,
                    "geo_fencing": geo_fencing,
                    "company_id": company_id,
                }
                return Response(result, status=200)
            else:
                return Response({"error": "Invalid credentials"}, status=401)
        else:
            return Response({"error": "Please provide Username and Password"})



User = get_user_model()

class ForgotPasswordAPIView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                # Generate a reset token and send email (dummy example)
                reset_link = f"http://yourdomain.com/reset-password/{user.pk}/dummy-token/"
                send_mail(
                    "Password Reset Request",
                    f"Click the link to reset your password: {reset_link}",
                    "no-reply@yourdomain.com",
                    [email],
                )
                return Response({"detail": "Password reset link sent to your email."}, status=200)
            except User.DoesNotExist:
                return Response({"error": "User with this email does not exist."}, status=404)
        return Response(serializer.errors, status=400)
    
class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = Employee.objects.filter(employee_user_id=request.user).first()
        if not employee:
            return Response({"error": "Employee profile not found."}, status=404)
        serializer = GetEmployeeSerializer(employee)
        return Response(serializer.data)