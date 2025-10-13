"""
Simplified AI Document Processing Models using LLM
Connects to Ollama LLM Server at http://125.18.84.108:11434/
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from horilla.models import HorillaModel
from base.horilla_company_manager import HorillaCompanyManager


class DocumentAIAnalysis(HorillaModel):
    """
    Simplified model to store LLM-based document analysis results
    """
    
    DOCUMENT_TYPES = [
        ('resume', _('Resume/CV')),
        ('other', _('Other Document')),
    ]
    
    EXTRACTION_STATUS = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    ]
    
    employee = models.ForeignKey(
        'employee.Employee',
        on_delete=models.CASCADE,
        related_name='ai_analyses',
        verbose_name=_("Employee")
    )
    document_file = models.FileField(
        upload_to='ai_analysis/%Y/%m/%d/',
        verbose_name=_("Document File")
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        default='resume',
        verbose_name=_("Document Type")
    )
    status = models.CharField(
        max_length=20,
        choices=EXTRACTION_STATUS,
        default='pending',
        verbose_name=_("Status")
    )
    
    # Extracted text content
    extracted_text = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Extracted Text")
    )
    
    # All extracted data in one JSON field (simplified)
    extracted_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Extracted Data")
    )
    
    # Confidence score from LLM
    confidence_score = models.FloatField(
        default=0.0,
        verbose_name=_("Confidence Score")
    )
    
    # Processing method info
    processing_method = models.CharField(
        max_length=50,
        default='ollama_llm',
        verbose_name=_("Processing Method")
    )
    
    # Error information if processing failed
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Error Message")
    )
    
    objects = HorillaCompanyManager(
        related_company_field="employee__employee_work_info__company_id"
    )
    
    class Meta:
        verbose_name = _("Document AI Analysis")
        verbose_name_plural = _("Document AI Analyses")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee} - {self.get_document_type_display()} - {self.status}"
    
    # Backward compatibility properties for existing code
    @property
    def personal_info(self):
        """Extract personal info from extracted_data for backward compatibility"""
        data = self.extracted_data or {}
        return {
            'name': data.get('name', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'city': data.get('city', ''),
        }
    
    @property
    def work_info(self):
        """Extract work info from extracted_data for backward compatibility"""
        data = self.extracted_data or {}
        return {
            'experience': data.get('experience', []),
            'total_experience_years': data.get('total_experience_years', 0),
        }
    
    @property
    def education_info(self):
        """Extract education info from extracted_data for backward compatibility"""
        data = self.extracted_data or {}
        return {
            'education': data.get('education', []),
        }


# Keep these models for backward compatibility but they won't be actively used
class AIExtractionField(HorillaModel):
    """
    Legacy model - kept for backward compatibility
    New implementation stores everything in DocumentAIAnalysis.extracted_data
    """
    
    analysis = models.ForeignKey(
        DocumentAIAnalysis,
        on_delete=models.CASCADE,
        related_name='extracted_fields',
        verbose_name=_("AI Analysis")
    )
    field_name = models.CharField(
        max_length=100,
        verbose_name=_("Field Name")
    )
    extracted_value = models.TextField(
        verbose_name=_("Extracted Value")
    )
    
    objects = HorillaCompanyManager(
        related_company_field="analysis__employee__employee_work_info__company_id"
    )
    
    class Meta:
        verbose_name = _("AI Extraction Field")
        verbose_name_plural = _("AI Extraction Fields")
    
    def __str__(self):
        return f"{self.analysis.employee} - {self.field_name}"


class AIProcessingLog(HorillaModel):
    """
    Simple logging model for AI processing
    """
    
    analysis = models.ForeignKey(
        DocumentAIAnalysis,
        on_delete=models.CASCADE,
        related_name='processing_logs',
        verbose_name=_("AI Analysis")
    )
    message = models.TextField(
        verbose_name=_("Message")
    )
    
    objects = HorillaCompanyManager(
        related_company_field="analysis__employee__employee_work_info__company_id"
    )
    
    class Meta:
        verbose_name = _("AI Processing Log")
        verbose_name_plural = _("AI Processing Logs")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.analysis.employee} - {self.message[:50]}"
