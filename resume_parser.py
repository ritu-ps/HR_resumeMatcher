import re
import PyPDF2
import docx
from typing import Dict, List, Any
import spacy
from datetime import datetime
class ResumeParser:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

        self.name_patterns = [
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$',
            r'([A-Z][a-z]+\s+[A-Z]\.?\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)'
        ]
      
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        self.phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
        self.education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'b.tech', 'm.tech',
            'b.e', 'm.e', 'b.sc', 'm.sc', 'b.a', 'm.a', 'b.b.a', 'm.b.a',
            'high school', 'diploma', 'certification', 'degree', 'university',
            'college', 'institute', 'school', 'education', 'academic'
        ]
    
    def parse(self, file) -> Dict[str, Any]:
        """
        Parse resume from uploaded file
        """
        text = self._extract_text(file)
        name = self._extract_name(text)
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        experience = self._extract_experience(text)
        education = self._extract_education(text)
        
        return {
            'name': name,
            'email': email,
            'phone': phone,
            'text': text,
            'experience': experience,
            'education': education,
            'processed_date': datetime.now().isoformat()
        }
    
    def _extract_text(self, file) -> str:
        """Extract text from PDF or DOCX file"""
        text = ""
        
        if file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(file)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        
        return text
    
    def _extract_name(self, text: str) -> str:
        """Extract candidate name from resume"""
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and len(line.split()) <= 4: 
                for pattern in self.name_patterns:
                    match = re.search(pattern, line)
                    if match:
                        return match.group(1)
        
        return "Unknown"
    
    def _extract_email(self, text: str) -> str:
        """Extract email from resume"""
        match = re.search(self.email_pattern, text)
        return match.group(0) if match else ""
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from resume"""
        match = re.search(self.phone_pattern, text)
        return match.group(0) if match else ""
    
    def _extract_experience(self, text: str) -> float:
        """Extract years of experience from resume"""
        exp_patterns = [
            r'(\d+)\+?\s*years? of experience',
            r'experience of (\d+)\+?\s*years?',
            r'total experience:?\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years? experience'
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1))
        
        doc = self.nlp(text)
        dates = []
        
        for ent in doc.ents:
            if ent.label_ == "DATE":
                date_text = ent.text.lower()
                year_match = re.search(r'\b(19|20)\d{2}\b', date_text)
                if year_match:
                    dates.append(int(year_match.group(0)))
        
        if len(dates) >= 2:
            return (max(dates) - min(dates)) 
        
        return 0.0
    
    def _extract_education(self, text: str) -> List[str]:
        """Extract education details from resume"""
        education = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()

            if any(keyword in line_lower for keyword in self.education_keywords):
                education.append(line.strip())
                
                for j in range(1, 4):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        if next_line and not any(keyword in next_line.lower() for keyword in ['experience', 'skill']):
                            if next_line not in education:
                                education.append(next_line)
        
        return education[:5]