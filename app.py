import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import base64
from datetime import datetime
import os
import sys
sys.path.append('.')

from utils.resume_parser import ResumeParser
from utils.skill_extractor import SkillExtractor
from utils.job_matcher import JobMatcher
from utils.question_gen import QuestionGenerator

# Page configuration
st.set_page_config(
    page_title="HR Resume Screening AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
def load_css():
    st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Card styling */
    .css-1r6slb0 {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    /* Header styling */
    h1 {
        color: #2c3e50;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    h2 {
        color: #34495e;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 600;
        border-bottom: 3px solid #3498db;
        padding-bottom: 0.5rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Success message styling */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid #27ae60;
    }
    
    /* Info box styling */
    .info-box {
        background: #f8f9fa;
        border-left: 4px solid #3498db;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Tag styling */
    .skill-tag {
        display: inline-block;
        background: #e1f5fe;
        color: #0288d1;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        margin: 0.2rem;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* Dashboard cards */
    .dashboard-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.15);
    }
    
    /* Score badges */
    .score-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        color: white;
    }
    
    .score-high {
        background: #27ae60;
    }
    
    .score-medium {
        background: #f39c12;
    }
    
    .score-low {
        background: #e74c3c;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main {
            padding: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'processed_resumes' not in st.session_state:
        st.session_state.processed_resumes = []
    if 'job_description' not in st.session_state:
        st.session_state.job_description = ""
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False

# Sidebar navigation
def sidebar_nav():
    with st.sidebar:
        # Logo and title
        st.image("https://img.icons8.com/color/96/000000/artificial-intelligence.png", width=80)
        st.title("HR AI Assistant")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigate to",
            ["📤 Upload & Match", "📊 Dashboard", "📝 Questions Generator", "📈 Analytics", "⚙️ Settings"]
        )
        
        st.markdown("---")
        
        # Quick stats
        st.subheader("Quick Stats")
        if st.session_state.processed_resumes:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Resumes", len(st.session_state.processed_resumes))
            with col2:
                avg_score = sum([r['match_score'] for r in st.session_state.processed_resumes]) / len(st.session_state.processed_resumes)
                st.metric("Avg Match", f"{avg_score:.1f}%")
        
        st.markdown("---")
        
        # Help section
        with st.expander("ℹ️ Help & Tips"):
            st.markdown("""
            - Upload PDF or DOCX resumes
            - Paste job description
            - Click 'Analyze' to process
            - View match scores
            - Generate interview questions
            """)
    
    return page

# Upload section
def upload_section():
    st.markdown("<h1 class='fade-in'>📄 Resume Screening & Job Matching</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📎 Upload Resumes")
        uploaded_files = st.file_uploader(
            "Drag and drop or click to upload",
            type=['pdf', 'docx'],
            accept_multiple_files=True,
            help="Upload multiple resumes in PDF or DOCX format"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} resume(s) uploaded successfully!")
            
            # File list with icons
            for file in uploaded_files:
                col1a, col1b = st.columns([3, 1])
                with col1a:
                    st.markdown(f"📄 {file.name}")
                with col1b:
                    file_size = len(file.getvalue()) / 1024
                    st.markdown(f"`{file_size:.1f} KB`")
    
    with col2:
        st.markdown("### 📋 Job Description")
        job_desc = st.text_area(
            "Paste the job description here",
            height=300,
            placeholder="Paste the complete job description including requirements, responsibilities, and qualifications..."
        )
        
        if job_desc:
            st.session_state.job_description = job_desc
            
            # JD Preview
            with st.expander("Preview Job Description"):
                st.markdown(job_desc[:500] + "..." if len(job_desc) > 500 else job_desc)
    
    # Analyze button
    if uploaded_files and job_desc:
        if st.button("🚀 Analyze Resumes", use_container_width=True):
            with st.spinner("Processing resumes... This may take a moment."):
                process_resumes(uploaded_files, job_desc)
                st.session_state.analysis_complete = True
                st.success("✅ Analysis complete!")
                st.balloons()

# Process resumes
def process_resumes(uploaded_files, job_desc):
    # Initialize processors
    resume_parser = ResumeParser()
    skill_extractor = SkillExtractor()
    job_matcher = JobMatcher()
    
    progress_bar = st.progress(0)
    
    for i, file in enumerate(uploaded_files):
        # Parse resume
        parsed_data = resume_parser.parse(file)
        
        # Extract skills
        skills = skill_extractor.extract_skills(parsed_data['text'])
        
        # Calculate match score
        match_result = job_matcher.calculate_match(skills, job_desc, parsed_data)
        
        # Store results
        result = {
            'name': parsed_data['name'],
            'email': parsed_data['email'],
            'phone': parsed_data['phone'],
            'skills': skills,
            'experience': parsed_data['experience'],
            'education': parsed_data['education'],
            'match_score': match_result['score'],
            'matched_skills': match_result['matched_skills'],
            'missing_skills': match_result['missing_skills'],
            'recommendations': match_result['recommendations']
        }
        
        st.session_state.processed_resumes.append(result)
        
        # Update progress
        progress_bar.progress((i + 1) / len(uploaded_files))

# Dashboard view
def dashboard_view():
    st.markdown("<h1 class='fade-in'>📊 Candidate Dashboard</h1>", unsafe_allow_html=True)
    
    if not st.session_state.processed_resumes:
        st.info("No resumes processed yet. Please upload and analyze resumes first.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class='dashboard-card'>
            <h3>Total Candidates</h3>
            <h2>{}</h2>
            <p>Processed resumes</p>
        </div>
        """.format(len(st.session_state.processed_resumes)), unsafe_allow_html=True)
    
    with col2:
        top_score = max([r['match_score'] for r in st.session_state.processed_resumes])
        st.markdown("""
        <div class='dashboard-card'>
            <h3>Top Match</h3>
            <h2>{:.1f}%</h2>
            <p>Highest score</p>
        </div>
        """.format(top_score), unsafe_allow_html=True)
    
    with col3:
        avg_score = sum([r['match_score'] for r in st.session_state.processed_resumes]) / len(st.session_state.processed_resumes)
        st.markdown("""
        <div class='dashboard-card'>
            <h3>Average</h3>
            <h2>{:.1f}%</h2>
            <p>Overall match</p>
        </div>
        """.format(avg_score), unsafe_allow_html=True)
    
    with col4:
        shortlisted = len([r for r in st.session_state.processed_resumes if r['match_score'] >= 70])
        st.markdown("""
        <div class='dashboard-card'>
            <h3>Shortlisted</h3>
            <h2>{}</h2>
            <p>Score ≥70%</p>
        </div>
        """.format(shortlisted), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Main candidates table
    st.subheader("📋 Candidates Ranking")
    
    # Create DataFrame
    df = pd.DataFrame(st.session_state.processed_resumes)
    df_display = df[['name', 'match_score', 'email', 'experience']].copy()
    df_display['match_score'] = df_display['match_score'].round(1)
    df_display = df_display.sort_values('match_score', ascending=False)
    
    # Style the dataframe
    def color_score(val):
        if val >= 70:
            return 'background-color: #d4edda'
        elif val >= 50:
            return 'background-color: #fff3cd'
        else:
            return 'background-color: #f8d7da'
    
    styled_df = df_display.style.applymap(color_score, subset=['match_score'])
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    st.markdown("---")
    
    # Detailed candidate view
    st.subheader("🔍 Candidate Details")
    
    selected_candidate = st.selectbox(
        "Select a candidate to view details",
        options=df['name'].tolist()
    )
    
    if selected_candidate:
        candidate = df[df['name'] == selected_candidate].iloc[0]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 📇 Personal Information")
            st.markdown(f"**Name:** {candidate['name']}")
            st.markdown(f"**Email:** {candidate['email']}")
            st.markdown(f"**Phone:** {candidate['phone']}")
            st.markdown(f"**Experience:** {candidate['experience']} years")
            
            st.markdown("#### 🎓 Education")
            for edu in candidate['education']:
                st.markdown(f"- {edu}")
        
        with col2:
            # Match score gauge
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = candidate['match_score'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Match Score"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#667eea"},
                    'steps': [
                        {'range': [0, 50], 'color': "#f8d7da"},
                        {'range': [50, 70], 'color': "#fff3cd"},
                        {'range': [70, 100], 'color': "#d4edda"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 70
                    }
                }
            ))
            
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
        
        # Skills section
        st.markdown("#### 💪 Skills Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**✅ Matched Skills**")
            for skill in candidate['matched_skills']:
                st.markdown(f"<span class='skill-tag'>{skill}</span>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("**❌ Missing Skills**")
            for skill in candidate['missing_skills']:
                st.markdown(f"<span class='skill-tag' style='background:#ffebee; color:#c62828;'>{skill}</span>", unsafe_allow_html=True)
        
        # Recommendations
        st.markdown("#### 💡 Recommendations")
        for rec in candidate['recommendations']:
            st.markdown(f"- {rec}")

# Questions generator
def questions_generator():
    st.markdown("<h1 class='fade-in'>📝 Interview Questions Generator</h1>", unsafe_allow_html=True)
    
    if not st.session_state.processed_resumes:
        st.info("Please analyze resumes first to generate personalized questions.")
        return
    
    question_gen = QuestionGenerator()
    
    # Candidate selection
    candidates = [r['name'] for r in st.session_state.processed_resumes]
    selected_candidate = st.selectbox("Select Candidate", candidates)
    
    # Question type selection
    question_types = st.multiselect(
        "Question Types",
        ["Technical", "Behavioral", "Situational", "Experience-based", "Cultural Fit"],
        default=["Technical", "Behavioral"]
    )
    
    # Difficulty level
    difficulty = st.select_slider(
        "Difficulty Level",
        options=["Beginner", "Intermediate", "Advanced", "Expert"],
        value="Intermediate"
    )
    
    # Number of questions
    num_questions = st.slider("Number of Questions", min_value=5, max_value=20, value=10)
    
    if st.button("🎯 Generate Questions", use_container_width=True):
        with st.spinner("Generating personalized questions..."):
            candidate_data = next(r for r in st.session_state.processed_resumes if r['name'] == selected_candidate)
            
            questions = question_gen.generate_questions(
                candidate_data,
                st.session_state.job_description,
                question_types,
                difficulty,
                num_questions
            )
            
            # Display questions
            st.markdown("---")
            st.markdown(f"### 📋 Interview Questions for {selected_candidate}")
            
            for i, q in enumerate(questions, 1):
                with st.expander(f"Question {i}: {q['type']} - {q['difficulty']}"):
                    st.markdown(f"**{q['question']}**")
                    
                    if 'follow_up' in q:
                        st.markdown("**Follow-up:**")
                        for fu in q['follow_up']:
                            st.markdown(f"- {fu}")
                    
                    if 'tips' in q:
                        st.markdown("**Interviewer Tips:**")
                        st.info(q['tips'])
            
            # Export options
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📄 Export as PDF"):
                    st.success("PDF export feature coming soon!")
            with col2:
                if st.button("📧 Email Questions"):
                    st.success("Email feature coming soon!")
            with col3:
                if st.button("💾 Save Template"):
                    st.success("Template saved!")

# Analytics view
def analytics_view():
    st.markdown("<h1 class='fade-in'>📈 Analytics Dashboard</h1>", unsafe_allow_html=True)
    
    if not st.session_state.processed_resumes:
        st.info("No data available for analytics.")
        return
    
    df = pd.DataFrame(st.session_state.processed_resumes)
    
    # Score distribution
    st.subheader("🎯 Score Distribution")
    fig = px.histogram(
        df, 
        x='match_score',
        nbins=20,
        title="Candidate Match Score Distribution",
        labels={'match_score': 'Match Score (%)'},
        color_discrete_sequence=['#667eea']
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Top skills analysis
    st.subheader("🔝 Most Common Skills")
    
    all_skills = []
    for skills in df['skills']:
        all_skills.extend(skills)
    
    skill_counts = pd.Series(all_skills).value_counts().head(10)
    
    fig = px.bar(
        x=skill_counts.values,
        y=skill_counts.index,
        orientation='h',
        title="Top 10 Skills Across Candidates",
        labels={'x': 'Frequency', 'y': 'Skills'},
        color=skill_counts.values,
        color_continuous_scale=['#667eea', '#764ba2']
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Experience distribution
    st.subheader("📊 Experience Distribution")
    fig = px.box(
        df,
        y='experience',
        title="Years of Experience Distribution",
        labels={'experience': 'Years of Experience'},
        color_discrete_sequence=['#667eea']
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Education breakdown
    st.subheader("🎓 Education Background")
    
    all_education = []
    for edu_list in df['education']:
        all_education.extend(edu_list)
    
    edu_counts = pd.Series(all_education).value_counts().head(8)
    
    fig = px.pie(
        values=edu_counts.values,
        names=edu_counts.index,
        title="Top Educational Backgrounds",
        color_discrete_sequence=px.colors.sequential.Purples_r
    )
    st.plotly_chart(fig, use_container_width=True)

# Settings view
def settings_view():
    st.markdown("<h1 class='fade-in'>⚙️ Settings</h1>", unsafe_allow_html=True)
    
    st.markdown("### 🎯 Matching Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.slider("Skills Weight", 0, 100, 60)
        st.slider("Experience Weight", 0, 100, 30)
        st.slider("Education Weight", 0, 100, 10)
    
    with col2:
        st.slider("Minimum Match Score", 0, 100, 50)
        st.checkbox("Enable AI Recommendations", value=True)
        st.checkbox("Auto-shortlist Top Candidates", value=True)
    
    st.markdown("### 🔧 Processing Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox("Resume Parsing Engine", ["Advanced AI", "Standard", "Fast"])
        st.selectbox("Skill Database", ["Built-in", "Custom", "Hybrid"])
    
    with col2:
        st.selectbox("Question Generation Model", ["GPT-4", "GPT-3.5", "Local Model"])
        st.number_input("Cache Timeout (minutes)", min_value=5, max_value=120, value=30)
    
    st.markdown("### 📧 Email Notifications")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("Send email on analysis complete", value=True)
        st.checkbox("Send daily summary", value=False)
    
    with col2:
        st.checkbox("Notify when top candidates found", value=True)
        st.checkbox("Send weekly reports", value=False)
    
    if st.button("💾 Save Settings", use_container_width=True):
        st.success("Settings saved successfully!")

# Main function
def main():
    # Load custom CSS
    load_css()
    
    # Initialize session state
    init_session_state()
    
    # Sidebar navigation
    page = sidebar_nav()
    
    # Main content area
    if page == "📤 Upload & Match":
        upload_section()
    elif page == "📊 Dashboard":
        dashboard_view()
    elif page == "📝 Questions Generator":
        questions_generator()
    elif page == "📈 Analytics":
        analytics_view()
    elif page == "⚙️ Settings":
        settings_view()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #7f8c8d; padding: 1rem;'>
            <p>🤖 HR AI Assistant - Powered by Advanced Machine Learning</p>
            <p style='font-size: 0.8rem;'>© 2024 All rights reserved</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()