from django.template.loader import render_to_string
from django import forms

from base.forms import ModelForm
from .models import FaceDetection


class FaceDetectionSetupForm(ModelForm):
    verbose_name = "Face Detection Configuration"

    class Meta:
        model = FaceDetection
        exclude = ["company_id"]
        fields = ['start']
        widgets = {
            'start': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for the start field
        self.fields['start'].help_text = "Enable face recognition attendance for this company"
        self.fields['start'].label = "Enable Face Detection"

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def as_p(self):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html
