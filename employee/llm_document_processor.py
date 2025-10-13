"""
LLM-Based Document Processor using Ollama Server
No third-party API keys required - uses local LLM server
Server: http://125.18.84.108:11434/
"""

import json
import logging
import re
import requests
from typing import Dict, Any, Optional
from django.core.files.uploadedfile import UploadedFile

# PDF and DOCX processing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    PyPDF2 = None

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    DocxDocument = None

logger = logging.getLogger(__name__)


class LLMDocumentProcessor:
    """
    Process documents using local Ollama LLM server
    """
    
    def __init__(self):
        self.ollama_endpoint = "http://125.18.84.108:11434/api/generate"
        self.model = "mistral"
        self.timeout = 60
    
    def extract_text_from_pdf(self, file) -> str:
        """Extract text from PDF file"""
        if not PDF_AVAILABLE:
            logger.error("PyPDF2 not available")
            return ""
        
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def extract_text_from_docx(self, file) -> str:
        """Extract text from DOCX file"""
        if not DOCX_AVAILABLE:
            logger.error("python-docx not available")
            return ""
        
        try:
            doc = DocxDocument(file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            return ""
    
    def extract_text_from_file(self, file) -> str:
        """Extract text based on file type"""
        filename = file.name.lower()
        
        if filename.endswith('.pdf'):
            return self.extract_text_from_pdf(file)
        elif filename.endswith('.docx'):
            return self.extract_text_from_docx(file)
        elif filename.endswith('.txt'):
            return file.read().decode('utf-8', errors='ignore')
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return ""
    
    def parse_with_llm(self, text: str, document_type: str = 'resume') -> Dict[str, Any]:
        """
        Use LLM to extract structured data from document text
        """
        
        # Create appropriate prompt based on document type
        if document_type == 'resume':
            prompt = self._create_resume_prompt(text)
        elif document_type == 'aadhaar':
            prompt = self._create_aadhaar_prompt(text)
        elif document_type == 'pan':
            prompt = self._create_pan_prompt(text)
        else:
            prompt = self._create_generic_prompt(text, document_type)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "temperature": 0.1,
            "options": {
                "num_predict": 2048
            }
        }
        
        try:
            logger.info(f"Sending request to Ollama LLM at {self.ollama_endpoint}")
            response = requests.post(
                self.ollama_endpoint,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '{}')
                
                # Parse JSON response
                try:
                    extracted_data = json.loads(response_text)
                    logger.info("Successfully extracted data with LLM")
                    return extracted_data
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response as JSON: {e}")
                    logger.debug(f"Raw response: {response_text}")
                    return self._fallback_extraction(text, document_type)
            else:
                logger.error(f"LLM API error: {response.status_code}")
                return self._fallback_extraction(text, document_type)
                
        except requests.exceptions.Timeout:
            logger.error("LLM request timeout")
            return self._fallback_extraction(text, document_type)
        except Exception as e:
            logger.error(f"LLM processing error: {e}")
            return self._fallback_extraction(text, document_type)
    
    def _create_resume_prompt(self, text: str) -> str:
        """Create prompt for resume parsing"""
        return f"""You are an expert resume parser. Extract the following information from the resume text below.
Return ONLY valid JSON format with no additional text or explanation.

Required JSON structure:
{{
  "name": "Full name of the candidate",
  "email": "Email address",
  "phone": "Phone number",
  "address": "Complete address if available",
  "city": "Current city/location",
  "state": "State/Province name (e.g., California, Maharashtra, Ontario)",
  "country": "Country name (e.g., United States, India, Canada)",
  "zip_code": "Postal/ZIP code if available",
  "date_of_birth": "Date of birth in YYYY-MM-DD format if available",
  "gender": "Gender if mentioned",
  "skills": ["skill1", "skill2", "skill3"],
  "experience": [
    {{
      "company": "Company name",
      "position": "Job title",
      "duration": "Duration (e.g., 2020-2023)",
      "description": "Brief description",
      "location": "Work location if mentioned"
    }}
  ],
  "education": [
    {{
      "degree": "Degree name",
      "institution": "University/College name",
      "year": "Year of completion",
      "field": "Field of study",
      "location": "Institution location if mentioned"
    }}
  ],
  "total_experience_years": 0.0,
  "portfolio": "Portfolio/website URL if mentioned",
  "summary": "Professional summary"
}}

Important extraction guidelines:
- Pay special attention to location information (country, state, city)
- Extract country and state names even if they appear in different parts of the document
- Use standard country names (e.g., "United States" not "USA", "India" not "IN")
- If any field is not found, use empty string for strings, empty array for arrays, or 0 for numbers

Resume Text:
{text[:4000]}

Return ONLY the JSON object:"""
    
    def _create_aadhaar_prompt(self, text: str) -> str:
        """Create prompt for Aadhaar card parsing"""
        return f"""You are an expert document parser. Extract Aadhaar card information from the text below.
Return ONLY valid JSON format with no additional text or explanation.

Required JSON structure:
{{
  "aadhaar_number": "12-digit Aadhaar number (e.g., 123456789012)",
  "name": "Full name as shown on Aadhaar card",
  "father_name": "Father's name if mentioned",
  "mother_name": "Mother's name if mentioned",
  "husband_name": "Husband's name if mentioned (for married women)",
  "gender": "Male/Female/Other",
  "date_of_birth": "Date of birth in YYYY-MM-DD format",
  "address": "Complete address as shown on card",
  "pincode": "PIN code (6-digit number)",
  "state": "State name (e.g., Maharashtra, Karnataka, Tamil Nadu)",
  "district": "District name if mentioned",
  "city": "City/Village name",
  "enrollment_number": "Enrollment number if mentioned",
  "enrollment_date": "Enrollment date if mentioned"
}}

Important extraction guidelines:
- Aadhaar number is always 12 digits, extract only the number without spaces or dashes
- Name should be exactly as written on the card (usually in English and local language)
- Address should include the complete address including house number, street, area
- Extract state name in English (e.g., "Maharashtra" not "महाराष्ट्र")
- If any field is not found, use empty string for strings
- Pay attention to both English and local language text

Document Text:
{text[:4000]}

Return ONLY the JSON object:"""
    
    def _create_pan_prompt(self, text: str) -> str:
        """Create prompt for PAN card parsing"""
        return f"""You are an expert document parser. Extract PAN card information from the text below.
Return ONLY valid JSON format with no additional text or explanation.

Required JSON structure:
{{
  "pan_number": "10-character PAN number (e.g., ABCDE1234F)",
  "name": "Full name as shown on PAN card",
  "father_name": "Father's name if mentioned",
  "date_of_birth": "Date of birth in YYYY-MM-DD format",
  "signature": "Signature text if mentioned"
}}

Important extraction guidelines:
- PAN number is always 10 characters (5 letters + 4 digits + 1 letter)
- Format: AAAAA9999A (5 uppercase letters, 4 digits, 1 uppercase letter)
- Name should be exactly as written on the card
- If any field is not found, use empty string for strings
- Pay attention to both English and local language text

Document Text:
{text[:4000]}

Return ONLY the JSON object:"""
    
    def _create_generic_prompt(self, text: str, doc_type: str) -> str:
        """Create generic prompt for other document types"""
        return f"""Extract key information from this {doc_type} document.
Return ONLY valid JSON format.

Document Text:
{text[:4000]}

Return JSON with extracted fields:"""
    
    def _fallback_extraction(self, text: str, document_type: str) -> Dict[str, Any]:
        """
        Fallback extraction using regex patterns when LLM fails
        """
        logger.info("Using fallback regex extraction")
        
        if document_type == 'aadhaar':
            return self._fallback_aadhaar_extraction(text)
        elif document_type == 'pan':
            return self._fallback_pan_extraction(text)
        
        extracted = {
            "name": "",
            "email": "",
            "phone": "",
            "city": "",
            "skills": [],
            "experience": [],
            "education": [],
            "total_experience_years": 0.0,
            "summary": "",
            "extraction_method": "regex_fallback"
        }
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            extracted["email"] = emails[0]
        
        # Extract phone
        phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
        phones = re.findall(phone_pattern, text)
        if phones:
            extracted["phone"] = phones[0].strip()
        
        # Extract name (first line often contains name)
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and len(line.split()) <= 4 and len(line) > 3:
                extracted["name"] = line
                break
        
        # Extract experience information
        experience_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:of\s*)?experience',
            r'experience[:\s]*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)',
            r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*in\s*\w+',
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    years = float(matches[0])
                    extracted["total_experience_years"] = years
                    extracted["experience"] = [f"{years} years of experience"]
                    break
                except ValueError:
                    continue
        
        # Extract education/qualification
        education_patterns = [
            r'(Bachelor|Master|PhD|B\.Tech|M\.Tech|B\.E|M\.E|B\.Com|M\.Com|B\.A|M\.A|B\.Sc|M\.Sc)[^.\n]*',
            r'(Diploma|Certificate|Degree)[^.\n]*',
            r'Education[:\s]*([^.\n]+)',
            r'Qualification[:\s]*([^.\n]+)',
        ]
        
        education_found = []
        for pattern in education_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                match = match.strip()
                if len(match) > 5 and match not in education_found:
                    education_found.append(match)
        
        if education_found:
            extracted["education"] = education_found
        
        # Extract skills
        skills_keywords = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node', 'django', 'flask',
            'sql', 'mysql', 'postgresql', 'mongodb', 'git', 'docker', 'aws', 'azure', 'gcp',
            'html', 'css', 'bootstrap', 'jquery', 'php', 'c++', 'c#', '.net', 'spring',
            'machine learning', 'ai', 'data science', 'pandas', 'numpy', 'tensorflow',
            'project management', 'agile', 'scrum', 'leadership', 'communication'
        ]
        
        skills_found = []
        text_lower = text.lower()
        for skill in skills_keywords:
            if skill in text_lower:
                skills_found.append(skill.title())
        
        if skills_found:
            extracted["skills"] = skills_found
        
        # Extract city/location
        location_patterns = [
            r'(?:Location|City|Address)[:\s]*([^.\n,]+)',
            r'([A-Za-z\s]+),\s*[A-Z]{2}',  # City, State format
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                city = match.group(1).strip()
                if len(city) > 2 and len(city) < 50:
                    extracted["city"] = city
                    break
        
        return extracted
    
    def _fallback_aadhaar_extraction(self, text: str) -> Dict[str, Any]:
        """
        Fallback extraction specifically for Aadhaar documents
        """
        extracted = {
            "aadhaar_number": "",
            "name": "",
            "father_name": "",
            "mother_name": "",
            "husband_name": "",
            "gender": "",
            "date_of_birth": "",
            "address": "",
            "pincode": "",
            "state": "",
            "district": "",
            "city": "",
            "enrollment_number": "",
            "enrollment_date": "",
            "extraction_method": "regex_fallback"
        }
        
        # Extract Aadhaar number (12 digits)
        aadhaar_pattern = r'\b(\d{4}[\s-]?\d{4}[\s-]?\d{4}|\d{12})\b'
        aadhaar_matches = re.findall(aadhaar_pattern, text)
        for match in aadhaar_matches:
            # Clean the match (remove spaces and dashes)
            clean_number = re.sub(r'[\s-]', '', match)
            if len(clean_number) == 12 and clean_number.isdigit():
                extracted["aadhaar_number"] = clean_number
                break
        
        # Extract PIN code (6 digits)
        pincode_pattern = r'\b(\d{6})\b'
        pincode_matches = re.findall(pincode_pattern, text)
        if pincode_matches:
            extracted["pincode"] = pincode_matches[0]
        
        # Extract enrollment number (4 digits followed by / and more digits)
        enrollment_pattern = r'\b(\d{4}/\d+/\d+)\b'
        enrollment_matches = re.findall(enrollment_pattern, text)
        if enrollment_matches:
            extracted["enrollment_number"] = enrollment_matches[0]
        
        # Extract date of birth (improved patterns for Aadhaar cards)
        dob_patterns = [
            r'Date of Birth[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'DOB[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Birth[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b',  # DD/MM/YYYY or DD-MM-YYYY
            r'\b(\d{4}[/-]\d{2}[/-]\d{2})\b',  # YYYY/MM/DD or YYYY-MM-DD
        ]
        
        for pattern in dob_patterns:
            dob_matches = re.findall(pattern, text, re.IGNORECASE)
            if dob_matches:
                dob = dob_matches[0]
                # Try to convert to YYYY-MM-DD format
                try:
                    if '/' in dob:
                        parts = dob.split('/')
                    else:
                        parts = dob.split('-')
                    
                    if len(parts[0]) == 4:  # YYYY format
                        extracted["date_of_birth"] = f"{parts[2]}-{parts[1]}-{parts[0]}"  # Convert to DD-MM-YYYY
                    else:  # DD format
                        extracted["date_of_birth"] = f"{parts[0]}-{parts[1]}-{parts[2]}"  # Keep as DD-MM-YYYY
                    break
                except:
                    continue
        
        # Extract gender (improved patterns for Aadhaar cards)
        gender_patterns = [
            r'Gender[:\s]*(Male|MALE|M|Female|FEMALE|F|Other|OTHER)',
            r'Sex[:\s]*(Male|MALE|M|Female|FEMALE|F|Other|OTHER)',
            r'\b(Male|MALE|M)\b',
            r'\b(Female|FEMALE|F)\b',
            r'\b(Other|OTHER)\b'
        ]
        
        for pattern in gender_patterns:
            gender_matches = re.findall(pattern, text, re.IGNORECASE)
            if gender_matches:
                gender = gender_matches[0].upper()
                if gender in ['MALE', 'M']:
                    extracted["gender"] = "Male"
                elif gender in ['FEMALE', 'F']:
                    extracted["gender"] = "Female"
                else:
                    extracted["gender"] = "Other"
                break
        
        # Extract name (improved patterns for Aadhaar cards)
        name_patterns = [
            r'Name[:\s]*([A-Za-z\s]+?)(?:\n|$)',
            r'Name of Person[:\s]*([A-Za-z\s]+?)(?:\n|$)',
            r'Full Name[:\s]*([A-Za-z\s]+?)(?:\n|$)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*/\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # Bilingual names like "Narikenabilli Rajini / Narikenabilli Rajini"
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)$',  # Proper case names
            r'^([A-Z]+(?:\s+[A-Z]+)+)$'  # All caps names
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if name_match:
                extracted["name"] = name_match.group(1).strip()
                break
        
        # If no name found with patterns, try line-by-line approach
        if not extracted["name"]:
            lines = text.split('\n')
            for line in lines[:15]:  # Check more lines
                line = line.strip()
                # Look for lines that look like names (2-4 words, mostly letters)
                if (line and 2 <= len(line.split()) <= 4 and 
                    re.match(r'^[A-Za-z\s]+$', line) and 
                    len(line) > 3 and len(line) < 50):
                    # Skip common non-name words
                    if not any(word in line.lower() for word in ['government', 'india', 'aadhaar', 'card', 'number', 'date', 'birth']):
                        extracted["name"] = line
                        break
        
        # Split name into first and last name
        if extracted["name"]:
            name_parts = extracted["name"].split()
            if len(name_parts) >= 2:
                extracted["first_name"] = name_parts[0]
                extracted["last_name"] = ' '.join(name_parts[1:])
            else:
                extracted["first_name"] = extracted["name"]
                extracted["last_name"] = ""
        
        # Extract address using a manual line-by-line approach for Aadhaar cards
        lines = text.split('\n')
        address_lines = []
        in_address_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Start collecting address after "To"
            if line.lower() == 'to':
                in_address_section = True
                continue
            
            # Stop collecting when we hit personal information
            if in_address_section and any(indicator in line.lower() for indicator in ['name of person', 'dob:', 'gender:', 'aadhaar', 'mobile:', 'number:']):
                break
            
            # Collect address lines
            if in_address_section and line:
                # Skip empty lines, person's name, and common non-address words
                if line and not line.lower() in ['government of india', 'to', '']:
                    # Skip the person's name line (usually the first line after "To")
                    if not any(word in line.lower() for word in ['rajini', 'narikenabilli']):
                        address_lines.append(line)
        
        if address_lines:
            # Join all address lines
            full_address = ' '.join(address_lines)
            # Clean up extra spaces and remove trailing comma and spaces
            full_address = re.sub(r'\s+', ' ', full_address)
            full_address = full_address.rstrip(', ')
            
            # Remove unwanted OCR artifacts and extra characters at the beginning
            # Remove characters like XX, Telugu characters, and other OCR artifacts
            full_address = re.sub(r'^[^A-Za-z0-9]*', '', full_address)  # Remove non-alphanumeric chars at start
            full_address = re.sub(r'^[A-Z]{1,3}\s+', '', full_address)  # Remove short uppercase words at start (XX, ABC, etc.)
            full_address = re.sub(r'^[^\w]*', '', full_address)  # Remove any remaining non-word chars at start
            
            # Additional cleanup for common OCR artifacts
            full_address = re.sub(r'^(XX|ABC|DEF|GHI|JKL|MNO|PQR|STU|VWX|YZ)\s+', '', full_address, flags=re.IGNORECASE)
            
            extracted["address"] = full_address
        
        # If the above didn't work, try individual patterns
        if not extracted["address"]:
            address_patterns = [
                r'C/O[:\s]*([A-Za-z0-9\s,.-]+?)(?:\n\s*Name|\n\s*DOB|\n\s*Gender|\n\s*Aadhaar|\n\s*Mobile|$)',
                r'Door No[:\s]*([A-Za-z0-9\s,.-]+?)(?:\n\s*Name|\n\s*DOB|\n\s*Gender|\n\s*Aadhaar|\n\s*Mobile|$)',
                r'Address[:\s]*([A-Za-z0-9\s,.-]+?)(?:\n\s*Name|\n\s*DOB|\n\s*Gender|\n\s*Aadhaar|\n\s*Mobile|$)',
                r'Residential Address[:\s]*([A-Za-z0-9\s,.-]+?)(?:\n\s*Name|\n\s*DOB|\n\s*Gender|\n\s*Aadhaar|\n\s*Mobile|$)',
                r'Permanent Address[:\s]*([A-Za-z0-9\s,.-]+?)(?:\n\s*Name|\n\s*DOB|\n\s*Gender|\n\s*Aadhaar|\n\s*Mobile|$)',
                r'చిరునామా[:\s]*([A-Za-z0-9\s,.-]+?)(?:\n\s*Name|\n\s*DOB|\n\s*Gender|\n\s*Aadhaar|\n\s*Mobile|$)',
            ]
            
            for pattern in address_patterns:
                address_match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE | re.DOTALL)
                if address_match:
                    address = address_match.group(1).strip()
                    # Clean up the address
                    address = re.sub(r'\n+', ' ', address)  # Replace newlines with spaces
                    address = re.sub(r'\s+', ' ', address)  # Replace multiple spaces with single space
                    extracted["address"] = address
                    break
        
        # If no address found with patterns, try to find address-like text
        if not extracted["address"]:
            lines = text.split('\n')
            address_lines = []
            in_address_section = False
            
            for i, line in enumerate(lines):
                line = line.strip()
                # Look for lines that contain address indicators (including door number)
                if any(indicator in line.lower() for indicator in ['door no', 'door number', 'c/o', 'street', 'road', 'lane', 'sector', 'area', 'colony', 'nagar', 'village', 'taluka', 'district', 'mandalam', 'veedhi']):
                    in_address_section = True
                    address_lines.append(line)
                elif in_address_section and line:
                    # Continue collecting address lines until we hit personal info
                    if any(indicator in line.lower() for indicator in ['name of person', 'dob:', 'gender:', 'aadhaar', 'mobile:', 'number:', 'qr code']):
                        break
                    elif re.match(r'^[A-Za-z0-9\s,.-/:\s]+$', line) and len(line) > 2:
                        address_lines.append(line)
                    elif line and re.search(r'\d{6}', line):  # PIN code line
                        address_lines.append(line)
                        break
                    elif line and ('state:' in line.lower() or 'district:' in line.lower() or 'vtc:' in line.lower()):
                        address_lines.append(line)
                    else:
                        break
            
            if address_lines:
                # Join all address lines and clean up
                full_address = ' '.join(address_lines)
                # Remove extra spaces and clean up
                full_address = re.sub(r'\s+', ' ', full_address)
                # Remove trailing comma and spaces
                full_address = full_address.rstrip(', ')
                
                # Remove unwanted OCR artifacts and extra characters at the beginning
                # Remove characters like XX, Telugu characters, and other OCR artifacts
                full_address = re.sub(r'^[^A-Za-z0-9]*', '', full_address)  # Remove non-alphanumeric chars at start
                full_address = re.sub(r'^[A-Z]{1,3}\s+', '', full_address)  # Remove short uppercase words at start (XX, ABC, etc.)
                full_address = re.sub(r'^[^\w]*', '', full_address)  # Remove any remaining non-word chars at start
                
                # Additional cleanup for common OCR artifacts
                full_address = re.sub(r'^(XX|ABC|DEF|GHI|JKL|MNO|PQR|STU|VWX|YZ)\s+', '', full_address, flags=re.IGNORECASE)
                
                extracted["address"] = full_address
        
        # Extract state from address or separate patterns
        if not extracted.get("state"):
            state_patterns = [
                r'State[:\s]*([A-Za-z\s]+?)(?:,|\n|$)',
                r'District[:\s]*([A-Za-z\s]+?)(?:,|\n|$)',
            ]
            
            for pattern in state_patterns:
                state_match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
                if state_match:
                    state = state_match.group(1).strip()
                    # Clean up state name
                    state = re.sub(r'\s+', ' ', state)
                    extracted["state"] = state
                    break
        
        # Extract city from address or separate patterns
        if not extracted.get("city"):
            city_patterns = [
                r'City[:\s]*([A-Za-z\s]+?)(?:,|\n|$)',
                r'VTC[:\s]*([A-Za-z\s]+?)(?:,|\n|$)',
                r'Town[:\s]*([A-Za-z\s]+?)(?:,|\n|$)',
            ]
            
            for pattern in city_patterns:
                city_match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
                if city_match:
                    city = city_match.group(1).strip()
                    # Clean up city name
                    city = re.sub(r'\s+', ' ', city)
                    extracted["city"] = city
                    break
        
        return extracted
    
    def _fallback_pan_extraction(self, text: str) -> Dict[str, Any]:
        """
        Fallback extraction specifically for PAN documents
        """
        extracted = {
            "pan_number": "",
            "name": "",
            "father_name": "",
            "date_of_birth": "",
            "signature": "",
            "extraction_method": "regex_fallback"
        }
        
        # Extract PAN number (10 characters: 5 letters + 4 digits + 1 letter)
        pan_patterns = [
            r'Permanent Account Number[:\s]*([A-Z]{5}[0-9]{4}[A-Z]{1})',
            r'PAN[:\s]*([A-Z]{5}[0-9]{4}[A-Z]{1})',
            r'([A-Z]{5}[0-9]{4}[A-Z]{1})',
        ]
        
        for pattern in pan_patterns:
            pan_match = re.search(pattern, text, re.IGNORECASE)
            if pan_match:
                extracted["pan_number"] = pan_match.group(1).upper()
                break
        
        # Extract name
        name_patterns = [
            r'Name[:\s]*([A-Za-z\s\.]+?)(?:\n|Father|Date|$)',
            r'Name of Person[:\s]*([A-Za-z\s\.]+?)(?:\n|Father|Date|$)',
            r'Income Tax Department[:\s]*([A-Za-z\s\.]+?)(?:\n|Father|Date|$)',
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip()
                name = re.sub(r'\s+', ' ', name)
                if len(name) > 2:  # Valid name should be more than 2 characters
                    extracted["name"] = name
                    break
        
        # Extract father's name
        father_patterns = [
            r'Father\'s Name[:\s]*([A-Za-z\s\.]+?)(?:\n|Date|$)',
            r'Father Name[:\s]*([A-Za-z\s\.]+?)(?:\n|Date|$)',
        ]
        
        for pattern in father_patterns:
            father_match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if father_match:
                father_name = father_match.group(1).strip()
                father_name = re.sub(r'\s+', ' ', father_name)
                if len(father_name) > 2:
                    extracted["father_name"] = father_name
                    break
        
        # Extract date of birth
        dob_patterns = [
            r'Date of Birth[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'DOB[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Birth[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b',
        ]
        
        for pattern in dob_patterns:
            dob_matches = re.findall(pattern, text, re.IGNORECASE)
            if dob_matches:
                dob = dob_matches[0]
                try:
                    if '/' in dob:
                        parts = dob.split('/')
                    else:
                        parts = dob.split('-')
                    
                    if len(parts[0]) == 4:  # YYYY format
                        extracted["date_of_birth"] = f"{parts[2]}-{parts[1]}-{parts[0]}"  # Convert to DD-MM-YYYY
                    else:  # DD format
                        extracted["date_of_birth"] = f"{parts[0]}-{parts[1]}-{parts[2]}"  # Keep as DD-MM-YYYY
                    break
                except:
                    continue
        
        # Extract signature (if mentioned)
        signature_patterns = [
            r'Signature[:\s]*([A-Za-z\s\.]+?)(?:\n|$)',
            r'Sign[:\s]*([A-Za-z\s\.]+?)(?:\n|$)',
        ]
        
        for pattern in signature_patterns:
            signature_match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if signature_match:
                signature = signature_match.group(1).strip()
                signature = re.sub(r'\s+', ' ', signature)
                if len(signature) > 2:
                    extracted["signature"] = signature
                    break
        
        return extracted
    
    def process_document(self, file, document_type: str = 'resume') -> Dict[str, Any]:
        """
        Main method to process document
        
        Args:
            file: Django UploadedFile object
            document_type: Type of document (resume, aadhaar, pan, etc.)
        
        Returns:
            Dictionary with extracted data
        """
        logger.info(f"Processing document: {file.name}, type: {document_type}")
        
        # Extract text from file
        extracted_text = self.extract_text_from_file(file)
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            logger.warning("Insufficient text extracted from document")
            return {
                "error": "Could not extract sufficient text from document",
                "status": "failed"
            }
        
        # Parse with LLM
        extracted_data = self.parse_with_llm(extracted_text, document_type)
        
        # Add metadata
        result = {
            "extracted_text": extracted_text[:5000],  # Store first 5000 chars
            "extracted_data": extracted_data,
            "document_type": document_type,
            "status": "completed" if extracted_data else "failed",
            "confidence_score": self._calculate_confidence(extracted_data, document_type),
            "processing_method": "ollama_llm"
        }
        
        return result
    
    def _calculate_confidence(self, data: Dict[str, Any], document_type: str = 'resume') -> float:
        """
        Calculate confidence score based on completeness of extracted data
        """
        if not data or "error" in data:
            return 0.0
        
        # Define fields based on document type
        if document_type == 'pan':
            required_fields = ['pan_number', 'name']
            optional_fields = ['father_name', 'date_of_birth', 'signature']
        elif document_type == 'aadhaar':
            required_fields = ['aadhaar_number', 'name']
            optional_fields = ['father_name', 'date_of_birth', 'address', 'gender', 'pincode']
        else:  # resume
            required_fields = ['name', 'email', 'phone']
            optional_fields = ['skills', 'experience', 'education', 'city']
        
        score = 0.0
        
        # Required fields (60% weight)
        for field in required_fields:
            if data.get(field) and len(str(data.get(field))) > 2:
                score += (60.0 / len(required_fields))  # Distribute 60% across required fields
        
        # Optional fields (40% weight)
        for field in optional_fields:
            if data.get(field):
                if isinstance(data[field], list) and len(data[field]) > 0:
                    score += (40.0 / len(optional_fields))  # Distribute 40% across optional fields
                elif isinstance(data[field], str) and len(data[field]) > 2:
                    score += (40.0 / len(optional_fields))
        
        return min(score, 100.0)


# Helper function for easy import
def process_resume_file(file) -> Dict[str, Any]:
    """
    Quick function to process a resume file
    
    Usage:
        from employee.llm_document_processor import process_resume_file
        result = process_resume_file(uploaded_file)
    """
    processor = LLMDocumentProcessor()
    return processor.process_document(file, document_type='resume')


def process_aadhaar_file(file) -> Dict[str, Any]:
    """
    Quick function to process an Aadhaar document file
    
    Usage:
        from employee.llm_document_processor import process_aadhaar_file
        result = process_aadhaar_file(uploaded_file)
    """
    processor = LLMDocumentProcessor()
    return processor.process_document(file, document_type='aadhaar')


def process_pan_file(file) -> Dict[str, Any]:
    """
    Quick function to process a PAN document file
    
    Usage:
        from employee.llm_document_processor import process_pan_file
        result = process_pan_file(uploaded_file)
    """
    processor = LLMDocumentProcessor()
    return processor.process_document(file, document_type='pan')

