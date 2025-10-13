
# AI Document Processing for Employee Module

This feature automatically extracts personal, work, and bank information from uploaded documents using local Python libraries only. No third-party API keys required.

## Features

- **Automatic Document Processing**: Upload resumes, certificates, bank statements, and other documents
- **Local Text Extraction**: Uses OCR and text processing libraries to extract structured data
- **Smart Field Mapping**: Automatically maps extracted data to employee fields
- **Confidence Scoring**: Shows confidence levels for extracted data
- **Manual Review**: Allows correction and verification of extracted data
- **Multiple Document Types**: Supports PDF, DOC, DOCX, JPG, PNG, TIFF files
- **No API Keys Required**: Works entirely with local Python libraries

## Supported Document Types

- **Resume/CV**: Extracts personal info, work experience, skills, education
- **Aadhaar Card**: Extracts personal details, Aadhaar number
- **PAN Card**: Extracts PAN number, personal details
- **Passport**: Extracts passport number, personal details
- **Bank Statement**: Extracts bank account details, transactions
- **Salary Slip**: Extracts salary information, work details
- **Offer Letter**: Extracts job details, salary, joining date
- **Employment Contract**: Extracts work terms, salary, dates
- **Certificates**: Extracts qualification details, dates

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install pytesseract PyPDF2 python-docx
```

### 2. Install Tesseract OCR (for image text extraction)

#### Windows:
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install the executable
3. Add Tesseract to your PATH environment variable

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

#### macOS:
```bash
brew install tesseract
```

### 3. Run Migrations

```bash
python manage.py makemigrations employee
python manage.py migrate
```

### 4. Test Installation

The system will automatically detect available libraries and use the best extraction method for each document type.

## Configuration

The system uses local Python libraries and requires no API keys. You can optionally configure settings in `synchr/employee/ai_settings.py`:

```python
# Tesseract OCR Settings (optional)
TESSERACT_PATH = None  # Auto-detect if None, or specify path like '/usr/bin/tesseract'

# Processing Settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/tiff',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
]

# Confidence Thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.7  # Stop processing at 70% confidence
MEDIUM_CONFIDENCE_THRESHOLD = 0.5
LOW_CONFIDENCE_THRESHOLD = 0.3
```

## Usage

### 1. Access AI Document Processing

1. Go to any employee's individual view
2. Click the settings menu (gear icon)
3. Select "AI Document Processing"

### 2. Upload Document

1. Select a document file (PDF, DOC, DOCX, JPG, PNG, TIFF)
2. Choose document type or let AI auto-detect
3. Click "Upload & Process"

### 3. Review Extracted Data

1. Wait for processing to complete
2. Review extracted information organized by type:
   - Personal Information
   - Work Information
   - Bank Information
3. Check confidence scores for each field
4. Edit any incorrect values

### 4. Apply Data

1. Select the fields you want to apply
2. Click "Apply Selected Fields" for each section
3. Data will be automatically populated in employee records

## API Endpoints

- `POST /employee/ai/upload/<employee_id>/` - Upload document
- `GET /employee/ai/analysis/<analysis_id>/status/` - Check processing status
- `GET /employee/ai/analysis/<analysis_id>/data/` - Get extracted data
- `POST /employee/ai/analysis/<analysis_id>/data/` - Apply extracted data
- `GET /employee/ai/employee/<employee_id>/analyses/` - List analyses
- `DELETE /employee/ai/analysis/<analysis_id>/delete/` - Delete analysis

## Models

### DocumentAIAnalysis
Stores AI analysis results for uploaded documents.

### AIExtractionField
Stores individual field extractions with confidence scores.

### AIProcessingLog
Logs AI processing activities and errors.

## Security Considerations

- File uploads are validated for type and size
- Sensitive data is stored securely
- Access is controlled by Django permissions
- API keys should be stored in environment variables

## Troubleshooting

### Common Issues

1. **OCR API Error**: Check API key and quota
2. **LLM Connection Error**: Ensure Ollama is running or API endpoint is accessible
3. **Low Confidence Scores**: Try higher quality documents
4. **Processing Timeout**: Large documents may take longer

### Debug Mode

Enable debug logging in Django settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'ai_processing.log',
        },
    },
    'loggers': {
        'employee.ai_services': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Performance Optimization

- Use SSD storage for better file I/O
- Consider using Redis for caching
- Implement background task processing for large files
- Use CDN for file storage

## Future Enhancements

- Support for more document types
- Batch processing capabilities
- Integration with cloud storage
- Advanced validation rules
- Custom field extraction templates
- Multi-language support
