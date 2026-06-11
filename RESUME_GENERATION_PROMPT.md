# ATS-Friendly Resume Generation Prompt

Use this prompt with any AI model (ChatGPT, Claude, etc.) to generate test resumes for the SBI Talent Intelligence System.

## Prompt Template

```
Generate 5 realistic, ATS-friendly resumes for candidates applying to data and analytics roles at SBI (State Bank of India). 
Each resume should be in plain text format suitable for parsing. Include:

- Full name at the top
- Email address
- Phone number (format: XXX-XXX-XXXX)
- Professional summary or objective (1-2 lines)
- Current role at current company
- Years of total experience
- Work experience section with 3-4 previous roles (include dates like "2020 - 2023")
- Education section (Bachelor's, Master's, or MBA)
- Technical skills (Python, SQL, Excel, Power BI, Tableau, AWS, Azure, Machine Learning, Data Analysis, etc.)
- Certifications (AWS, Azure, GCP, CFA, PMP, etc.)
- Key projects with brief descriptions
- One candidate should have 2+ years experience
- One candidate should have 5+ years experience
- One candidate should have 8+ years experience
- One candidate should have banking/finance domain experience
- One candidate should have AI/ML specialization

Format each resume as plain text with clear section headers like:
JOHN DOE
Email: john.doe@email.com
Phone: 555-123-4567

PROFESSIONAL SUMMARY
Data analyst with 5 years of experience...

CURRENT ROLE
Senior Data Analyst at XYZ Corporation

EXPERIENCE
Senior Data Analyst | ABC Corp | 2021 - Present
- Developed dashboards using Power BI and Tableau
- Analyzed customer behavior data and improved retention by 15%

Data Analyst | DEF Inc | 2018 - 2021
- Performed ETL operations using SQL
- Created reports in Excel and Power Query

EDUCATION
Master of Business Administration (MBA) | University Name | 2018
Bachelor of Science in Statistics | University Name | 2016

SKILLS
Python, R, SQL, Excel, Power BI, Tableau, AWS, Machine Learning, Data Visualization, 
Business Intelligence, Statistical Analysis, Apache Spark, Hadoop

CERTIFICATIONS
AWS Certified Data Analytics - Specialty
Microsoft Certified: Data Analyst Associate
Google Cloud Professional Data Engineer

PROJECTS
Project 1: Customer Segmentation Analysis
- Used clustering algorithms (K-means) on customer purchase data
- Identified 5 distinct customer segments for targeted marketing
- Results led to 12% increase in campaign ROI

Project 2: Sales Forecasting Model
- Built predictive model using Python and scikit-learn
- Achieved 92% accuracy in quarterly sales forecasting
- Model adopted across all regional offices

---

Generate 5 such diverse resumes. Make them realistic and varied in experience levels, domains, and specializations.
```

## How to Use

1. Copy the prompt above
2. Paste it into ChatGPT, Claude, Gemini, or any AI model
3. The model will generate 5 realistic ATS-friendly resumes
4. Copy each resume and save as a `.txt` file or paste into a text editor
5. Convert each `.txt` resume to PDF using Word or any online converter
6. Upload the PDFs to the SBI Talent Intelligence System via the Streamlit interface

## Expected Output

Each generated resume will contain:
- ✅ Name, email, phone
- ✅ Current role and company
- ✅ Years of experience
- ✅ Education details
- ✅ Multiple skills (easily parseable)
- ✅ Certifications
- ✅ Project descriptions
- ✅ Work history with dates

## Variations to Request

You can modify the prompt to generate resumes with:
- **"Include 1 resume with no certifications"**
- **"Include 1 resume with 15+ years experience"**
- **"Include 1 resume focused on cloud technologies (AWS, Azure, GCP)"**
- **"Include 1 resume with domain expertise in Insurance/Banking"**
- **"Include 1 resume with leadership/management experience"**
- **"Include international candidates with H-1B or visa sponsorship mention"**

## Testing the App

Once you have the test resumes as PDFs:

1. Open the Streamlit app (http://localhost:8501)
2. Upload the PDFs in the sidebar
3. The app will:
   - Extract candidate information
   - Parse skills, certifications, education
   - Store data in SQLite
   - Index content for semantic search
4. Test features:
   - Dashboard (view statistics)
   - Candidate Explorer (filter by skill, education)
   - Semantic Search (e.g., "Python developers with AWS")
   - Candidate Ranking (paste a job description)
   - RAG Chat (ask questions about candidates)
