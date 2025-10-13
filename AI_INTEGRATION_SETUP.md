# AI Document Processing Integration Setup

## Overview
This guide will help you set up AI-powered document processing for the Sync HRMS employee and recruitment modules. The system can automatically extract personal information, work details, bank information, and education data from uploaded documents.

## Features Implemented

### Employee Module
- **AI Document Upload Page**: `/employee/ai/upload-page/<employee_id>/`
- **Automatic Field Extraction**: Personal info, work info, bank info, education info
- **Document Types Supported**: Resume, Aadhaar, PAN, Passport, Bank Statement, Salary Slip, Offer Letter, Contract, Certificate
- **Modern UI**: Drag-and-drop interface with real-time processing status
- **Enhanced Resume Parsing**: Uses [pyresparser](https://pypi.org/project/pyresparser/) for more accurate resume data extraction

### Recruitment Module
- **Enhanced Resume Processing**: Both `resume_completion` and `matching_resume_completion` functions now use AI
- **Automatic Form Filling**: Extracts comprehensive candidate information
- **Fallback Support**: Falls back to regex-based extraction if AI fails

## Server Configuration

### Current AI Server Endpoint
The system is configured to use your Ollama server:
- **Endpoint**: `http://125.18.84.108:11434/api/generate`
- **Model**: `mistral`

### Testing the Connection
Run the test script to verify connectivity:
```bash
cd synchr
python test_ai_endpoint.py
```

## Setup Instructions

### 1. Ensure AI Server is Running
Make sure your Ollama server at `http://125.18.84.108:11434` is:
- Running and accessible
- Has the `mistral` model installed
- Accepts external connections

### 2. Install Required Dependencies
Run the automated installation script:
```bash
cd synchr
python install_ocr_dependencies.py
```

Or install manually:
```bash
pip install requests pillow pytesseract PyPDF2 pyresparser spacy nltk
```

### 2.1. Install pyresparser Dependencies (for Enhanced Resume Parsing)
Use the Django management command:
```bash
python manage.py install_pyresparser
```

Or install manually:
```bash
pip install pyresparser spacy nltk
python -m spacy download en_core_web_sm
python -m nltk.downloader words
```

### 3. Database Migration
Run migrations to create AI-related tables:
```bash
python manage.py makemigrations employee
python manage.py migrate
```

### 4. OCR Setup (Optional)
For better document processing, install Tesseract OCR:
- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
- **Linux**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`

### 5. Test pyresparser Integration
Run the integration test:
```bash
python test_pyresparser_integration.py
```

## Usage

### Employee Module
1. Navigate to any employee's profile
2. Go to the AI Document Processing page
3. Upload documents (PDF, DOC, DOCX, JPG, PNG, TIFF)
4. Select document type or use auto-detection
5. Review extracted information
6. Apply data to employee fields

### Recruitment Module
1. Go to recruitment application form
2. Upload a resume
3. The form will automatically fill with AI-extracted data
4. Review and modify as needed

## Configuration Files

### AI Settings (`employee/ai_settings.py`)
```python
# LLM Settings
LLM_ENDPOINT = 'http://125.18.84.108:11434/api/generate'
LLM_MODEL = 'mistral'

# OCR Settings (optional)
OCR_API_KEY = 'your_ocr_api_key_here'
OCR_API_URL = 'https://api.ocr.space/parse/image'
```

### Field Mappings
The system includes comprehensive field mappings for:
- Personal information
- Work details
- Bank information
- Education/certificate data

## Troubleshooting

### Common Issues

1. **AI Endpoint Not Accessible**
   - Check if the server is running
   - Verify network connectivity
   - Ensure firewall allows connections

2. **OCR Not Working (403 Forbidden Error)**
   - **FIXED**: The system now has multiple OCR fallback methods
   - OCR.space API is disabled by default (no API key required)
   - System automatically falls back to PyPDF2 for PDF text extraction
   - For better image OCR, install Tesseract OCR
   - Test OCR functionality: `python test_simple_ocr.py`

3. **Document Processing Failed**
   - **FIXED**: Improved error handling with specific feedback
   - For PDF files, try converting to image format (JPG/PNG) for better results
   - Ensure documents are clear and readable
   - Check file size (max 10MB)

4. **Database Errors**
   - Run migrations: `python manage.py migrate`
   - Check database permissions
   - Verify model imports

### Debug Mode
Enable debug logging by adding to your Django settings:
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

## API Endpoints

### Employee AI Endpoints
- `POST /employee/ai/upload/<employee_id>/` - Upload and process document
- `GET /employee/ai/analysis/<analysis_id>/status/` - Check processing status
- `GET /employee/ai/analysis/<analysis_id>/data/` - Get extracted data
- `POST /employee/ai/analysis/<analysis_id>/apply/` - Apply extracted data
- `DELETE /employee/ai/analysis/<analysis_id>/delete/` - Delete analysis

### Recruitment AI Integration
- `POST /recruitment/resume-completion/` - Enhanced resume processing
- `GET /recruitment/matching-resume-completion/` - Enhanced matching resume processing

## Security Considerations

1. **API Keys**: Store sensitive API keys in environment variables
2. **File Uploads**: Validate file types and sizes
3. **Data Privacy**: Ensure extracted data is handled securely
4. **Network Security**: Use HTTPS in production

## Performance Optimization

1. **Caching**: Implement Redis caching for frequent requests
2. **Async Processing**: Use Celery for background processing
3. **File Storage**: Use cloud storage for large files
4. **Database Indexing**: Add indexes for frequently queried fields

## Support

For issues or questions:
1. Check the logs in `ai_processing.log`
2. Run the test script: `python test_ai_endpoint.py`
3. Verify server connectivity
4. Check Django error logs

## Future Enhancements

- Support for more document types
- Batch processing capabilities
- Advanced field validation
- Machine learning model training
- Multi-language support
- Cloud AI service integration
