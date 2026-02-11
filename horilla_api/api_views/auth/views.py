from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail

from ...api_serializers.auth.serializers import GetEmployeeSerializer, ForgotPasswordSerializer, ResetPasswordSerializer, ChangePasswordSerializer
from employee.models import Employee


User = get_user_model()
token_generator = PasswordResetTokenGenerator()


class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        if "username" in request.data.keys() and "password" in request.data.keys():
            username = request.data.get("username")
            password = request.data.get("password")
            user = authenticate(username=username, password=password)
            if user:
                refresh = RefreshToken.for_user(user)
                try:
                    # Use related_name 'employee_get' from the model definition
                    employee = getattr(user, 'employee_get', None)
                    if not employee:
                        # Fallback search if reverse relation is missing
                        employee = Employee.objects.filter(employee_user_id=user).first()
                except Exception as e:
                    print(f"Error retrieving employee for user {user.username}: {str(e)}")
                    return Response({"error": f"Employee record retrieval failed: {str(e)}"}, status=500)

                if not employee:
                    return Response({"error": "No Employee record associated with this user."}, status=400)

                face_detection = False
                face_detection_image = None
                geo_fencing = False
                company_id = None
                
                try:
                    company = employee.get_company()
                    if company:
                        company_id = company.id
                        try:
                            face_detection = getattr(company.face_detection, 'start', False)
                        except: pass
                        try:
                            geo_fencing = getattr(company.geo_fencing, 'start', False)
                        except: pass
                except:
                    pass

                try:
                    face_detection_image = employee.face_detection.image.url
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


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            # Filter users by email
            users = User.objects.filter(email=email)
            if users.exists():
                # Prioritize user where username matches email
                user = users.filter(username=email).first()
                if not user:
                    # If no exact username match, take the first one found
                    user = users.first()
            if user:
                # Generate secure token using Django's PasswordResetTokenGenerator
                token = token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Build reset URL using FRONTEND_URL from settings
                frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
                reset_link = f"{frontend_url}/reset-password/{uid}/{token}"
                
                # Send email with reset link
                send_mail(
                    subject="Password Reset Request - HRMS",
                    message=f"Click the link to reset your password: {reset_link}\n\nThis link will expire in 24 hours.\n\nIf you did not request this, please ignore this email.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            # Return same message regardless of user existence to prevent email enumeration
            return Response({"detail": "Password reset link sent to your email."}, status=200)
        return Response(serializer.errors, status=400)


class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            uid = serializer.validated_data['uid']
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                # Decode the user ID
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
                
                # Validate the token
                if not token_generator.check_token(user, token):
                    return Response({"error": "Invalid or expired reset link."}, status=400)
                
                # Set new password
                user.set_password(new_password)
                user.save()
                
                return Response({"detail": "Password has been reset successfully."}, status=200)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response({"error": "Invalid reset link."}, status=400)
        return Response(serializer.errors, status=400)


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']

            if not user.check_password(old_password):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = getattr(request.user, 'employee_get', None)
        if not employee:
            employee = Employee.objects.filter(employee_user_id=request.user).first()
            
        if not employee:
            return Response({"error": "Employee profile not found."}, status=404)
            
        serializer = GetEmployeeSerializer(employee)
        return Response(serializer.data)


class GroupsListView(APIView):
    """List Django auth Groups for employee filter (employee_user_id__groups)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        groups = Group.objects.all().order_by('name')
        data = [{"id": g.id, "name": g.name} for g in groups]
        return Response(data)


class PermissionsListView(APIView):
    """List Django auth Permissions for employee filter (employee_user_id__user_permissions)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perms = Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'codename')
        data = [{"id": p.id, "codename": p.codename, "name": p.name or p.codename} for p in perms]
        return Response(data)