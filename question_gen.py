from typing import List, Dict, Any
import random
import json


class QuestionGenerator:
    def __init__(self):
        self.question_templates = self._load_templates()

    def _load_templates(self) -> Dict[str, List[str]]:
        """Load question templates for different types"""
        return {
            'technical': [
                "Can you explain your experience with {skill}?",
                "What projects have you worked on using {skill}?",
                "How would you troubleshoot a {skill} related issue?",
                "Describe a challenging problem you solved using {skill}",
                "What best practices do you follow when working with {skill}?"
            ],
            'behavioral': [
                "Tell me about a time when you had to {action}",
                "Describe a situation where you {action}",
                "Give an example of how you {action}",
                "How do you handle {situation}?",
                "Describe your approach to {action}"
            ],
            'situational': [
                "What would you do if {scenario}?",
                "How would you handle {situation}?",
                "Describe how you would approach {task}",
                "What steps would you take to {action}?"
            ],
            'experience': [
                "Can you walk me through your experience with {skill}?",
                "What was your role in the {project} project?",
                "How did you contribute to {achievement}?",
                "What challenges did you face while working on {project}?"
            ],
            'cultural_fit': [
                "What type of work environment do you prefer?",
                "How do you handle conflicts in a team?",
                "Describe your ideal company culture",
                "How do you stay updated with industry trends?"
            ]
        }

    def generate_questions(
        self,
        candidate_data: Dict[str, Any],
        job_description: str,
        question_types: List[str],
        difficulty: str,
        num_questions: int
    ) -> List[Dict[str, Any]]:

        questions = []

        skills = candidate_data.get('skills', [])
        missing_skills = candidate_data.get('missing_skills', [])
        experience = candidate_data.get('experience', 0)

        for q_type in question_types:
            type_questions = self._generate_type_questions(
                q_type.lower(),
                skills,
                missing_skills,
                job_description,
                difficulty,
                max(1, num_questions // len(question_types))
            )
            questions.extend(type_questions)

        random.shuffle(questions)
        questions = questions[:num_questions]

        for i, q in enumerate(questions, 1):
            q['id'] = i
            q['difficulty'] = difficulty

        return questions

    def _safe_format(self, template: str, **kwargs) -> str:
        """
        Safely format template without KeyError
        """
        placeholders = {
            "skill": kwargs.get("skill", "this technology"),
            "action": kwargs.get("action", "handle the situation"),
            "situation": kwargs.get("situation", "a difficult situation"),
            "scenario": kwargs.get("scenario", "a challenging scenario"),
            "task": kwargs.get("task", "the task"),
            "project": kwargs.get("project", "project"),
            "achievement": kwargs.get("achievement", "a key achievement")
        }

        return template.format(**placeholders)

    def _generate_type_questions(
        self,
        q_type: str,
        skills: List[str],
        missing_skills: List[str],
        job_description: str,
        difficulty: str,
        count: int
    ) -> List[Dict]:

        questions = []
        templates = self.question_templates.get(q_type, [])

        if not templates:
            return questions

        if q_type == 'technical':

            focus_skills = skills[:3] + missing_skills[:2]

            for skill in focus_skills[:count]:
                template = random.choice(templates)

                question = self._safe_format(template, skill=skill)

                questions.append({
                    'type': q_type.capitalize(),
                    'question': question,
                    'follow_up': self._generate_follow_ups(q_type, skill, difficulty)
                })

        elif q_type == 'behavioral':

            actions = [
                'lead a team',
                'handle a difficult situation',
                'meet a tight deadline',
                'deal with conflict',
                'learn a new technology',
                'improve a process',
                'mentor someone',
                'handle criticism',
                'work under pressure'
            ]

            for _ in range(min(count, len(actions))):

                action = random.choice(actions)
                template = random.choice(templates)

                question = self._safe_format(
                    template,
                    action=action,
                    situation=action
                )

                questions.append({
                    'type': q_type.capitalize(),
                    'question': question,
                    'tips': self._get_interview_tips(q_type, difficulty)
                })

        elif q_type == 'situational':

            scenarios = [
                'a project deadline is approaching and a team member falls ill',
                'you discover a critical bug just before release',
                'a client requests a feature that was not in scope',
                'you have conflicting priorities from stakeholders',
                'a team member disagrees with your technical approach'
            ]

            for scenario in scenarios[:count]:

                template = random.choice(templates)

                question = self._safe_format(
                    template,
                    scenario=scenario,
                    situation=scenario,
                    action="resolve the issue",
                    task=scenario
                )

                questions.append({
                    'type': q_type.capitalize(),
                    'question': question,
                    'follow_up': [
                        "What would be your first step?",
                        "How would you communicate this?"
                    ]
                })

        elif q_type == 'experience':

            projects = ["AI resume screening system", "web platform", "data pipeline"]

            for project in projects[:count]:

                template = random.choice(templates)

                question = self._safe_format(
                    template,
                    project=project,
                    skill=random.choice(skills) if skills else "a technology",
                    achievement="a successful outcome"
                )

                questions.append({
                    'type': q_type.capitalize(),
                    'question': question
                })

        elif q_type == 'cultural_fit':

            for template in templates[:count]:

                questions.append({
                    'type': q_type.capitalize(),
                    'question': template
                })

        return questions

    def _generate_follow_ups(self, q_type: str, context: str, difficulty: str) -> List[str]:

        follow_ups = {
            'technical': [
                f"What specific challenges have you faced with {context}?",
                f"How do you stay updated with {context}?",
                f"What alternatives to {context} have you considered?",
                f"How would you teach {context} to a junior developer?"
            ],
            'behavioral': [
                "What was the outcome?",
                "What did you learn from this experience?",
                "Would you do anything differently next time?",
                "How did others react to your approach?"
            ]
        }

        return follow_ups.get(q_type, [])[:2]

    def _get_interview_tips(self, q_type: str, difficulty: str) -> str:

        tips = {
            'technical': "Look for specific examples and depth of knowledge.",
            'behavioral': "Use the STAR method (Situation, Task, Action, Result).",
            'situational': "Focus on the thought process and decision-making.",
            'experience': "Verify the candidate's real contribution.",
            'cultural_fit': "Assess alignment with company values."
        }

        return tips.get(q_type, "")

    def export_questions(self, questions: List[Dict], format: str = 'json') -> str:

        if format == 'json':
            return json.dumps(questions, indent=2)

        elif format == 'text':

            text = "Interview Questions\n" + "=" * 50 + "\n\n"

            for q in questions:

                text += f"Q{q['id']}. [{q['type']} - {q['difficulty']}]\n"
                text += f"{q['question']}\n\n"

                if 'follow_up' in q:
                    text += "Follow-up questions:\n"
                    for fu in q['follow_up']:
                        text += f" • {fu}\n"

                text += "-" * 50 + "\n\n"

            return text