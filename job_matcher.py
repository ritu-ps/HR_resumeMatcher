from typing import Dict, List, Tuple, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

class JobMatcher:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000
        )
        
        # Weights for different components
        self.weights = {
            'skills': 0.5,
            'experience': 0.3,
            'education': 0.2
        }
    
    def calculate_match(self, 
                       candidate_skills: List[str], 
                       job_description: str,
                       candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate match score between candidate and job description
        """
        # Extract skills from job description
        jd_skills = self._extract_jd_skills(job_description)
        
        # Calculate skills match
        skills_result = self._match_skills(candidate_skills, jd_skills)
        
        # Calculate experience match
        experience_result = self._match_experience(
            candidate_data.get('experience', 0),
            job_description
        )
        
        # Calculate education match
        education_result = self._match_education(
            candidate_data.get('education', []),
            job_description
        )
        
        # Calculate overall score
        overall_score = (
            skills_result['score'] * self.weights['skills'] +
            experience_result['score'] * self.weights['experience'] +
            education_result['score'] * self.weights['education']
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            skills_result,
            experience_result,
            education_result
        )
        
        return {
            'score': round(overall_score * 100, 2),
            'matched_skills': skills_result['matched'],
            'missing_skills': skills_result['missing'],
            'recommendations': recommendations
        }
    
    def _extract_jd_skills(self, job_description: str) -> List[str]:
        """Extract skills mentioned in job description"""
        # Common skill indicators in job descriptions
        skill_patterns = [
            r'required skills?:?\s*([^\n]+)',
            r'qualifications?:?\s*([^\n]+)',
            r'experience with:?\s*([^\n]+)',
            r'proficient in:?\s*([^\n]+)',
            r'knowledge of:?\s*([^\n]+)'
        ]
        
        skills = set()
        jd_lower = job_description.lower()
        
        # Extract from specific sections
        for pattern in skill_patterns:
            matches = re.findall(pattern, jd_lower)
            for match in matches:
                # Split by common separators
                parts = re.split(r'[,\|\•\-\s]+', match)
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 2:  # Ignore very short strings
                        skills.add(part)
        
        # Also look for capitalized terms that might be skills
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', job_description)
        skills.update([w.lower() for w in words if len(w) > 2])
        
        return list(skills)
    
    def _match_skills(self, candidate_skills: List[str], jd_skills: List[str]) -> Dict:
        """Calculate skills match"""
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        jd_skills_lower = [s.lower() for s in jd_skills]
        
        matched = []
        missing = []
        
        # Find matches (allow partial matches)
        for jd_skill in jd_skills_lower:
            found = False
            for cand_skill in candidate_skills_lower:
                if jd_skill in cand_skill or cand_skill in jd_skill:
                    matched.append(jd_skill)
                    found = True
                    break
            if not found:
                missing.append(jd_skill)
        
        # Calculate score
        if jd_skills:
            score = len(matched) / len(jd_skills)
        else:
            score = 0.5  # Default if no skills specified
        
        return {
            'score': score,
            'matched': matched[:10],  # Limit to top 10
            'missing': missing[:10]    # Limit to top 10
        }
    
    def _match_experience(self, candidate_exp: float, job_description: str) -> Dict:
        """Calculate experience match"""
        # Extract required experience from job description
        exp_patterns = [
            r'(\d+)[\+]?\s*years? of experience',
            r'experience of (\d+)[\+]?\s*years?',
            r'minimum of (\d+)[\+]?\s*years?',
            r'at least (\d+)[\+]?\s*years?'
        ]
        
        required_exp = 0
        for pattern in exp_patterns:
            match = re.search(pattern, job_description.lower())
            if match:
                required_exp = float(match.group(1))
                break
        
        if required_exp == 0:
            return {'score': 0.5}  # Default if not specified
        
        if candidate_exp >= required_exp:
            # More experience is better, but with diminishing returns
            bonus = min((candidate_exp - required_exp) * 0.05, 0.2)
            score = min(1.0 + bonus, 1.2)
        else:
            # Less experience reduces score
            score = max(candidate_exp / required_exp, 0)
        
        return {
            'score': min(score, 1.0),  # Cap at 1.0
            'required': required_exp,
            'candidate': candidate_exp
        }
    
    def _match_education(self, candidate_edu: List[str], job_description: str) -> Dict:
        """Calculate education match"""
        # Education level scoring
        edu_levels = {
            'high school': 1,
            'diploma': 2,
            'bachelor': 3,
            'master': 4,
            'phd': 5,
            'doctorate': 5
        }
        
        # Find highest education level in candidate
        candidate_level = 0
        for edu in candidate_edu:
            edu_lower = edu.lower()
            for level, value in edu_levels.items():
                if level in edu_lower:
                    candidate_level = max(candidate_level, value)
        
        # Find required education from job description
        required_level = 0
        jd_lower = job_description.lower()
        for level, value in edu_levels.items():
            if level in jd_lower:
                required_level = max(required_level, value)
        
        if required_level == 0:
            return {'score': 0.5}  # Default if not specified
        
        if candidate_level >= required_level:
            score = 1.0
        else:
            score = candidate_level / required_level
        
        return {
            'score': score,
            'required_level': required_level,
            'candidate_level': candidate_level
        }
    
    def _generate_recommendations(self, 
                                 skills_result: Dict,
                                 experience_result: Dict,
                                 education_result: Dict) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Skills recommendations
        if skills_result['missing']:
            missing_str = ', '.join(skills_result['missing'][:3])
            recommendations.append(f"Consider upskilling in: {missing_str}")
        
        # Experience recommendations
        if 'required' in experience_result:
            if experience_result.get('candidate', 0) < experience_result.get('required', 0):
                diff = experience_result['required'] - experience_result['candidate']
                recommendations.append(
                    f"Gain {diff:.1f} more years of relevant experience"
                )
        
        # Education recommendations
        if 'required_level' in education_result:
            if education_result.get('candidate_level', 0) < education_result.get('required_level', 0):
                recommendations.append(
                    "Consider pursuing higher education or relevant certifications"
                )
        
        # General recommendations
        if skills_result['score'] < 0.5:
            recommendations.append(
                "Focus on acquiring core skills mentioned in the job description"
            )
        
        return recommendations[:5] 