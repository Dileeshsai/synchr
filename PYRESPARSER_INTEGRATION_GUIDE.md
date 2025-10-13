# pyresparser Integration Guide for Sync HRMS

## Overview

This guide explains how to integrate [pyresparser](https://pypi.org/project/pyresparser/) with Sync HRMS for enhanced resume parsing capabilities. pyresparser is a specialized library that provides more accurate extraction of resume data compared to generic OCR methods.

## What is pyresparser?

pyresparser is a Python library specifically designed for parsing resumes and extracting structured information. It uses spaCy and NLTK for natural language processing to accurately identify:

- **Personal Information**: Name, email, phone number
- **Experience**: Total years of experience, company names, designations
- **Education**: College names, degrees, qualifications
- **Skills**: Technical and soft skills
- **Contact Details**: Email, mobile numbers

## Benefits of pyresparser Integration

### Before Integration (Current Issues)
Based on your uploaded resume example, the current system had these inaccuracies:
- **City**: `agra` (incorrect)
- **Country**: `usa` (incorrect) 
- **Experience**: `3.8` (should be calculated from internship period)
- **Qualification**: `Secondary School Certificate)` (should be B. Tech)

### After Integration (Expected Improvements)
With pyresparser, you should get:
- **Name**: `Narikenabilli Rajini` (accurate)
- **Email**: `rajinin7805@gmail.com` (accurate)
- **Phone**: `+91 9676668421` (accurate)
- **Experience**: Calculated from work history (more accurate)
- **Education**: `B. Tech (Computer Science and Engineering)` (accurate)
- **Skills**: `Java, Python, Django, Agentic AI, HTML, CSS, JavaScript` (comprehensive)
- **Company**: `TANASV TECHNOLOGIES PVT LTD` (accurate)

## Installation

### Method 1: Automated Installation (Recommended)
```bash
cd synchr
python install_pyresparser_dependencies.py
```

### Method 2: Django Management Command
```bash
python manage.py install_pyresparser
```

### Method 3: Manual Installation
```bash
# Install Python packages
pip install pyresparser spacy nltk

# Download spaCy English model
python -m spacy download en_core_web_sm

# Download NLTK words corpus
python -m nltk.downloader words
```

## Testing the Integration

### 1. Run Integration Test
```bash
python test_pyresparser_integration.py
```

### 2. Test with Sample Resume
1. Place a sample resume (PDF or DOCX) in the project root
2. Run the test script
3. Check the extracted data

### 3. Test in HRMS Interface
1. Go to `/employee/ai/upload-page/<employee_id>/`
2. Upload a resume
3. Check the extracted fields and confidence scores

## How It Works

### Processing Flow
```
Resume Upload → Document Classification → pyresparser Extraction → Field Mapping → Database Storage
```

### Integration Points

1. **Primary Method**: For resumes, pyresparser is used first
2. **Fallback Method**: If pyresparser fails or has low confidence, falls back to original AI extraction
3. **Confidence Threshold**: pyresparser data is used if confidence > 70%

### Code Changes Made

1. **Added pyresparser import** in `ai_services.py`
2. **Created `_extract_with_pyresparser()` function** for resume parsing
3. **Modified resume processing logic** to use pyresparser first
4. **Added field mapping** from pyresparser format to HRMS format
5. **Updated requirements.txt** with new dependencies
6. **Created installation scripts** and test utilities

## Configuration

### Confidence Thresholds
- **pyresparser**: 70% (high confidence required)
- **Fallback AI**: 60% (lower threshold for fallback)

### Supported File Formats
- **PDF**: Full support
- **DOCX**: Full support  
- **DOC**: Requires textract (optional)

### Field Mapping
```python
pyresparser → HRMS Format
name → first_name + last_name
email → email
mobile_number → phone
total_experience → experience
college_name → institution
degree → qualification
company_names → company
designation → job_position
skills → skills (comma-separated)
```

## Troubleshooting

### Common Issues

#### 1. Import Error: No module named 'pyresparser'
**Solution**: Install pyresparser
```bash
pip install pyresparser
```

#### 2. spaCy Model Not Found
**Solution**: Download the English model
```bash
python -m spacy download en_core_web_sm
```

#### 3. NLTK Data Not Found
**Solution**: Download NLTK data
```bash
python -m nltk.downloader words
```

#### 4. Low Confidence Scores
**Causes**:
- Poor quality resume (scanned images)
- Unusual resume format
- Missing text content

**Solutions**:
- Use high-quality PDF/DOCX files
- Ensure resume has clear text (not just images)
- Check if resume follows standard format

### Debug Mode
Enable debug logging to see detailed extraction process:
```python
# In Django settings
LOGGING = {
    'loggers': {
        'employee.ai_services': {
            'level': 'DEBUG',
        },
    },
}
```

## Performance Considerations

### Processing Time
- **pyresparser**: ~2-5 seconds per resume
- **Fallback AI**: ~5-10 seconds per resume
- **Total**: Usually under 10 seconds

### Memory Usage
- **spaCy model**: ~50MB
- **NLTK data**: ~10MB
- **Processing**: ~100MB per resume

### Optimization Tips
1. **Cache spaCy model**: Load once, reuse for multiple resumes
2. **Batch processing**: Process multiple resumes together
3. **Async processing**: Use Celery for background processing

## API Usage

### Direct Usage
```python
from pyresparser import ResumeParser

# Parse a resume
data = ResumeParser('/path/to/resume.pdf').get_extracted_data()
print(data[0])  # First result
```

### With Custom Skills File
```python
# Create custom skills CSV file
parser = ResumeParser('/path/to/resume.pdf', skills_file='/path/to/skills.csv')
data = parser.get_extracted_data()
```

### With Custom Regex
```python
# Custom phone number pattern
parser = ResumeParser('/path/to/resume.pdf', custom_regex=r'\+91-\d{10}')
data = parser.get_extracted_data()
```

## Monitoring and Logs

### AI Processing Logs
Check the admin panel at `/admin/employee/documentaianalysis/` to see:
- Extraction method used (pyresparser vs AI)
- Confidence scores
- Processing time
- Error messages

### Log Levels
- **INFO**: Successful extractions
- **WARNING**: Fallback to AI method
- **ERROR**: Complete extraction failure

## Future Enhancements

### Planned Improvements
1. **Custom Skills Database**: Company-specific skills recognition
2. **Multi-language Support**: Support for resumes in different languages
3. **Batch Processing**: Process multiple resumes simultaneously
4. **Confidence Tuning**: Adjust thresholds based on results
5. **Custom Field Mapping**: Allow custom field extraction rules

### Integration Opportunities
1. **Recruitment Module**: Enhanced candidate data extraction
2. **Employee Onboarding**: Automatic profile creation from resumes
3. **Skills Matching**: Match candidates to job requirements
4. **Analytics**: Resume parsing statistics and insights

## Support and Resources

### Documentation
- [pyresparser PyPI](https://pypi.org/project/pyresparser/)
- [spaCy Documentation](https://spacy.io/)
- [NLTK Documentation](https://www.nltk.org/)

### Community
- [pyresparser GitHub](https://github.com/omkarpathak27/pyresparser)
- [spaCy GitHub](https://github.com/explosion/spaCy)
- [NLTK GitHub](https://github.com/nltk/nltk)

### Sync HRMS Support
- Check AI processing logs in admin panel
- Run integration tests: `python test_pyresparser_integration.py`
- Review extraction results in employee AI upload page

---

## Quick Start Checklist

- [ ] Install pyresparser: `pip install pyresparser spacy nltk`
- [ ] Download spaCy model: `python -m spacy download en_core_web_sm`
- [ ] Download NLTK data: `python -m nltk.downloader words`
- [ ] Test installation: `python test_pyresparser_integration.py`
- [ ] Upload a test resume in HRMS
- [ ] Check extracted data accuracy
- [ ] Monitor AI processing logs

**🎉 You're now ready to use enhanced resume parsing with pyresparser!**
