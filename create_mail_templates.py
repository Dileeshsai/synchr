#!/usr/bin/env python
"""
Script to create useful HRMS mail templates
Run with: python manage.py shell < create_mail_templates.py
Or: python create_mail_templates.py (if Django is set up)
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from base.models import HorillaMailTemplate

templates = [
    {
        'title': 'Welcome Email - New Employee Onboarding',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<h2 style="color: #2c3e50; margin-bottom: 20px;">Welcome to {{instance.get_company}}!</h2>
<p>Dear {{instance.get_full_name}},</p>
<p>We are thrilled to welcome you to our team as <strong>{{instance.get_job_position}}</strong>!</p>
<p>Your journey with us begins today, and we are excited about the contributions you will make to our organization.</p>
<h3 style="color: #3498db; margin-top: 25px;">Your Details:</h3>
<ul style="line-height: 1.8;">
<li><strong>Employee ID:</strong> {{instance.badge_id}}</li>
<li><strong>Department:</strong> {{instance.get_department}}</li>
<li><strong>Job Position:</strong> {{instance.get_job_position}}</li>
<li><strong>Employee Type:</strong> {{instance.get_employee_type}}</li>
</ul>
<p style="margin-top: 25px;">If you have any questions, please don't hesitate to reach out to your manager or HR department.</p>
<p>Best regards,<br><strong>{{self.get_full_name}}</strong><br>HR Department<br>{{instance.get_company}}</p>
</div>
</div>'''
    },
    {
        'title': 'Leave Request Approval',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<h2 style="color: #27ae60; margin-bottom: 20px;">✓ Leave Request Approved</h2>
<p>Dear {{instance.get_full_name}},</p>
<p>Your leave request has been <strong>approved</strong>.</p>
<p>We hope you have a restful time off and look forward to your return.</p>
<p>If you have any questions, please contact your manager.</p>
<p>Best regards,<br><strong>{{self.get_full_name}}</strong><br>{{instance.get_company}}</p>
</div>
</div>'''
    },
    {
        'title': 'Leave Request Rejection',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<h2 style="color: #e74c3c; margin-bottom: 20px;">Leave Request Update</h2>
<p>Dear {{instance.get_full_name}},</p>
<p>We regret to inform you that your leave request could not be approved at this time due to operational requirements.</p>
<p>Please contact your manager to discuss alternative dates or any concerns you may have.</p>
<p>Best regards,<br><strong>{{self.get_full_name}}</strong><br>{{instance.get_company}}</p>
</div>
</div>'''
    },
    {
        'title': 'Performance Review Reminder',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<h2 style="color: #3498db; margin-bottom: 20px;">Performance Review Scheduled</h2>
<p>Dear {{instance.get_full_name}},</p>
<p>This is a reminder that your performance review is scheduled.</p>
<p>Please prepare by reviewing your goals and achievements for this period.</p>
<p>If you have any questions or need to reschedule, please contact your manager.</p>
<p>Best regards,<br><strong>{{self.get_full_name}}</strong><br>HR Department<br>{{instance.get_company}}</p>
</div>
</div>'''
    },
    {
        'title': 'Birthday Wishes',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); color: white; text-align: center;">
<h1 style="margin: 0; font-size: 32px;">🎉 Happy Birthday! 🎉</h1>
<h2 style="margin-top: 20px;">{{instance.get_full_name}}</h2>
<p style="font-size: 18px; margin-top: 20px;">Wishing you a wonderful day filled with joy and happiness!</p>
<p style="margin-top: 30px;">From all of us at <strong>{{instance.get_company}}</strong></p>
</div>
</div>'''
    },
    {
        'title': 'Work Anniversary',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;">
<h2 style="color: #e67e22; margin-bottom: 20px;">🎊 Congratulations on Your Work Anniversary! 🎊</h2>
<p>Dear {{instance.get_full_name}},</p>
<p>We are honored to celebrate another year of your dedication and contribution to <strong>{{instance.get_company}}</strong>.</p>
<p>Your commitment to excellence and teamwork has made a significant impact on our organization.</p>
<p>Thank you for being an invaluable member of our team!</p>
<p>Best regards,<br><strong>{{self.get_full_name}}</strong><br>Management Team<br>{{instance.get_company}}</p>
</div>
</div>'''
    },
    {
        'title': 'Policy Update Notification',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<h2 style="color: #34495e; margin-bottom: 20px;">Important Policy Update</h2>
<p>Dear {{instance.get_full_name}},</p>
<p>This is to inform you that there has been an update to company policies.</p>
<p>Please review the updated policies in the HRMS system and ensure you are familiar with the changes.</p>
<p>If you have any questions, please contact the HR department.</p>
<p>Best regards,<br><strong>{{self.get_full_name}}</strong><br>HR Department<br>{{instance.get_company}}</p>
</div>
</div>'''
    },
    {
        'title': 'Attendance Reminder',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<h2 style="color: #f39c12; margin-bottom: 20px;">Attendance Reminder</h2>
<p>Dear {{instance.get_full_name}},</p>
<p>This is a friendly reminder to ensure you mark your attendance daily.</p>
<p>Regular attendance tracking helps us maintain accurate records and ensures smooth operations.</p>
<p>If you face any issues with attendance marking, please contact your manager or HR.</p>
<p>Best regards,<br><strong>{{self.get_full_name}}</strong><br>HR Department<br>{{instance.get_company}}</p>
</div>
</div>'''
    },
    {
        'title': 'Document Request',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<h2 style="color: #3498db; margin-bottom: 20px;">Document Request</h2>
<p>Dear {{instance.get_full_name}},</p>
<p>We require certain documents from you for our records.</p>
<p>Please submit the requested documents at your earliest convenience through the HRMS portal or contact HR for assistance.</p>
<p>If you have any questions, please don't hesitate to reach out.</p>
<p>Best regards,<br><strong>{{self.get_full_name}}</strong><br>HR Department<br>{{instance.get_company}}</p>
</div>
</div>'''
    },
    {
        'title': 'Shift Change Notification',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<h2 style="color: #9b59b6; margin-bottom: 20px;">Shift Schedule Update</h2>
<p>Dear {{instance.get_full_name}},</p>
<p>This is to inform you that there has been a change to your shift schedule.</p>
<p>Please check your updated schedule in the HRMS system.</p>
<p>If you have any concerns or questions, please contact your manager.</p>
<p>Best regards,<br><strong>{{self.get_full_name}}</strong><br>HR Department<br>{{instance.get_company}}</p>
</div>
</div>'''
    },
    {
        'title': 'Payroll Notification',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<h2 style="color: #16a085; margin-bottom: 20px;">Payslip Available</h2>
<p>Dear {{instance.get_full_name}},</p>
<p>Your payslip for this month is now available in the HRMS system.</p>
<p>Please log in to view and download your payslip. If you have any questions regarding your payslip, please contact the payroll department.</p>
<p>Best regards,<br><strong>{{self.get_full_name}}</strong><br>Payroll Department<br>{{instance.get_company}}</p>
</div>
</div>'''
    },
    {
        'title': 'Training Program Invitation',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<h2 style="color: #8e44ad; margin-bottom: 20px;">Training Program Invitation</h2>
<p>Dear {{instance.get_full_name}},</p>
<p>You have been selected to participate in an upcoming training program that will enhance your skills and contribute to your professional development.</p>
<p>Details about the training schedule and venue will be shared shortly. Please confirm your participation at your earliest convenience.</p>
<p>Best regards,<br><strong>{{self.get_full_name}}</strong><br>Learning & Development<br>{{instance.get_company}}</p>
</div>
</div>'''
    },
    {
        'title': 'Meeting Reminder',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<h2 style="color: #2980b9; margin-bottom: 20px;">Meeting Reminder</h2>
<p>Dear {{instance.get_full_name}},</p>
<p>This is a reminder that you have a scheduled meeting.</p>
<p>Please ensure you are prepared and available at the scheduled time.</p>
<p>If you need to reschedule, please inform the organizer as soon as possible.</p>
<p>Best regards,<br><strong>{{self.get_full_name}}</strong><br>{{instance.get_company}}</p>
</div>
</div>'''
    },
    {
        'title': 'Sudden Leave Announcement',
        'body': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<h2 style="color: #e67e22; margin-bottom: 20px;">⚠️ Sudden Leave Announcement</h2>
<p>Dear Team,</p>
<p>This is to inform you that <strong>{{instance.get_full_name}}</strong> (<strong>{{instance.get_job_position}}</strong>) will be on leave due to an unexpected situation.</p>
<div style="margin: 20px 0; padding: 15px; background: #fff3cd; border-left: 4px solid #e67e22; border-radius: 6px;">
<p style="margin: 6px 0;"><strong>Employee:</strong> {{instance.get_full_name}}</p>
<p style="margin: 6px 0;"><strong>Department:</strong> {{instance.get_department}}</p>
<p style="margin: 6px 0;"><strong>Reason:</strong> [Please specify the reason for sudden leave]</p>
<p style="margin: 6px 0;"><strong>Expected Return:</strong> [Please specify expected return date]</p>
</div>
<p>During this period, please direct any urgent matters to their manager or the HR department.</p>
<p>We appreciate your understanding and will keep you updated on any changes.</p>
<p>Best regards,<br><strong>{{self.get_full_name}}</strong><br>HR Department<br>{{instance.get_company}}</p>
</div>
</div>'''
    }
]

created_count = 0
updated_count = 0

for template_data in templates:
    template, created = HorillaMailTemplate.objects.get_or_create(
        title=template_data['title'],
        defaults={
            'body': template_data['body'],
            'is_active': True
        }
    )
    if created:
        created_count += 1
        print(f"[+] Created: {template_data['title']}")
    else:
        # Update existing template
        template.body = template_data['body']
        template.is_active = True
        template.save()
        updated_count += 1
        print(f"[*] Updated: {template_data['title']}")

print(f"\n{'='*50}")
print(f"Summary: Created {created_count} templates, Updated {updated_count} templates")
print(f"Total templates processed: {len(templates)}")
print(f"{'='*50}")
