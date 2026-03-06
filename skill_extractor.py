import re
from typing import List, Set, Dict
import spacy
from collections import Counter


class SkillExtractor:
    def __init__(self):

        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

        # Technical skills categories
        self.tech_categories = {
            'programming_languages': [
                'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift',
                'kotlin', 'typescript', 'go', 'rust', 'scala', 'perl', 'r', 'matlab'
            ],
            'frameworks': [
                'django', 'flask', 'spring', 'react', 'angular', 'vue', 'node.js',
                'express', 'tensorflow', 'pytorch', 'keras', 'pandas', 'numpy',
                'scikit-learn', 'hadoop', 'spark', 'laravel', 'rails'
            ],
            'databases': [
                'sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'redis',
                'elasticsearch', 'cassandra', 'dynamodb', 'firebase', 'mariadb'
            ],
            'cloud': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
                'terraform', 'ansible', 'puppet', 'chef', 'cloudformation'
            ],
            'tools': [
                'git', 'jira', 'confluence', 'slack', 'trello', 'asana',
                'postman', 'selenium', 'junit', 'maven', 'gradle', 'webpack'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving',
                'analytical', 'project management', 'time management', 'creativity',
                'adaptability', 'critical thinking', 'collaboration', 'presentation'
            ]
        }

        # Load skills database AFTER categories are defined
        self.skills_database = self._load_skills_database()

    def _load_skills_database(self) -> Set[str]:
        """Load comprehensive skills database"""
        skills = set()

        # Flatten all categories
        for category, skill_list in self.tech_categories.items():
            skills.update(skill_list)

        # Add common variations
        variations = {
            'js': 'javascript',
            'ts': 'typescript',
            'py': 'python',
            'cplusplus': 'c++',
            'csharp': 'c#',
            'node': 'node.js',
            'reactjs': 'react',
            'angularjs': 'angular',
            'vuejs': 'vue',
            'postgres': 'postgresql',
            'mongo': 'mongodb',
            'dynamo': 'dynamodb',
            'elastic': 'elasticsearch',
            'k8s': 'kubernetes'
        }

        skills.update(variations.keys())

        return skills

    def extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from resume text
        """
        text_lower = text.lower()
        found_skills = set()

        # Pattern-based extraction
        for skill in self.skills_database:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)

        # NLP-based extraction
        doc = self.nlp(text)

        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()

            if any(word in chunk_text for word in ['experience', 'knowledge', 'proficient', 'skill']):
                words = chunk_text.split()
                for word in words:
                    if word in self.skills_database:
                        found_skills.add(word)

        # Extract from bullet points
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()

            if any(indicator in line_lower for indicator in ['skills:', 'technologies:', 'expertise:']):
                skill_parts = re.split(r'[,\|\•\-\s]+', line_lower)

                for part in skill_parts:
                    part = part.strip()
                    if part in self.skills_database:
                        found_skills.add(part)

        return sorted(list(found_skills))

    def categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorize skills by type"""

        categorized = {
            'programming_languages': [],
            'frameworks': [],
            'databases': [],
            'cloud': [],
            'tools': [],
            'soft_skills': [],
            'other': []
        }

        for skill in skills:
            skill_lower = skill.lower()
            found = False

            for category, category_skills in self.tech_categories.items():
                if skill_lower in category_skills:
                    categorized[category].append(skill)
                    found = True
                    break

            if not found:
                categorized['other'].append(skill)

        return categorized

    def get_skill_frequency(self, resumes_data: List[Dict]) -> Dict[str, int]:
        """Get frequency of skills across multiple resumes"""

        all_skills = []

        for resume in resumes_data:
            all_skills.extend(resume.get('skills', []))

        return dict(Counter(all_skills))

    def suggest_skills(self, job_description: str, current_skills: List[str]) -> List[str]:
        """Suggest relevant skills based on job description"""

        jd_lower = job_description.lower()

        jd_skills = []
        for skill in self.skills_database:
            if skill in jd_lower:
                jd_skills.append(skill)

        current_skills_lower = [s.lower() for s in current_skills]

        missing_skills = [s for s in jd_skills if s not in current_skills_lower]

        return missing_skills[:10]