<!-- LLM-CONTEXT-START -->
- **Document Type**: Product Requirements Document (PRD)
- **Applies To**: Interview Evaluator Application
- **Audience**: Development Team, Product Managers, Stakeholders
- **Latest Update**: 2024-07-26
<!-- LLM-CONTEXT-END -->

# Product Requirements Document: AI Interview Evaluator

## 1. Introduction

This document outlines the requirements for the AI Interview Evaluator application. The goal is to build a tool that assists interviewers by processing interview transcripts and providing an objective evaluation of data scientist candidates based on their responses. The application will leverage LLMs, LangGraph, and LlamaIndex for analysis, with a Node.js frontend and Supabase for backend services.

## 2. Goals

-   Streamline the interview feedback process.
-   Provide objective, consistent candidate evaluations based on predefined criteria.
-   Reduce interviewer time spent manually reviewing transcripts and writing detailed feedback.
-   Create a persistent record of interview evaluations.

## 3. User Stories

-   **As an Interviewer, I want to:**
    -   Upload an interview transcript file (e.g., .txt, .vtt, .docx).
    -   Have the system automatically parse the transcript to identify questions and answers.
    -   Define or select evaluation criteria/topics relevant to the role (e.g., Python proficiency, SQL skills, ML concepts, communication).
    -   Receive a structured evaluation report highlighting candidate strengths and weaknesses per criterion.
    -   See specific quotes from the transcript justifying the evaluation points.
    -   View an overall assessment or score for the candidate.
    -   Securely log in to access the application.
    -   View past evaluations.

## 4. Features

### 4.1 MVP (Minimum Viable Product)

-   **Transcript Upload:** Ability to upload transcript files (.txt).
-   **Transcript Parsing:** Use LlamaIndex to parse the transcript, identifying speaker turns and content. Basic Q&A pair extraction.
-   **Evaluation Criteria:** Predefined, non-editable criteria for core data science skills (e.g., Python, SQL, Statistics, ML Theory, Communication).
-   **LangGraph Agent:** Workflow to process parsed transcript, apply evaluation criteria using an LLM, and generate scores/justifications per criterion.
-   **Evaluation Report:** Simple display of evaluation results (scores, justifications per criterion, overall summary).
-   **Supabase Integration:**
    -   Store interview metadata and evaluation results in Postgres.
    -   Basic user authentication.
-   **Basic Frontend:** Functional UI (Node.js/Tailwind) for upload and displaying results.
-   **Backend API:** FastAPI service to handle requests from the frontend and orchestrate the Python logic.

### 4.2 Post-MVP / Future Enhancements

-   **Customizable Criteria:** Allow users to define and weight evaluation criteria.
-   **Multiple File Formats:** Support for .vtt, .docx, .pdf transcripts.
-   **Advanced Parsing:** Improved Q&A extraction, handling interruptions, identifying follow-up questions.
-   **Comparative Analysis:** Compare candidates interviewed for the same role.
-   **Role Templates:** Predefined sets of criteria for different roles (Data Scientist, ML Engineer, Data Analyst).
-   **Real-time Processing:** (Ambitious) Process audio streams directly.
-   **Feedback Loop:** Allow interviewers to rate the quality of the AI evaluation.
-   **Graph Database Integration:** Explore using graph structures if complex relationship analysis between skills/topics becomes valuable.

## 5. Technical Architecture

-   **Frontend:** ReactJS/TypeScript, Tailwind CSS, HTML.
-   **Backend API:** Python (FastAPI).
-   **AI/ML:**
    -   LangGraph (Agentic Workflow Orchestration, deployed to LangChain Cloud).
    -   LlamaIndex (Transcript Parsing, Structured Data Extraction).
    -   LLM (GPT-4 with OpenAI API - configurable via Langchain).
    -   LangSmith for monitoring and tracing (optional).
-   **Database:** Supabase Postgres.
-   **Authentication:** Supabase Auth.
-   **Hosting:**
    -   Frontend: Vercel.
    -   LangGraph Agent: LangChain Cloud.
    -   Backend API: Render / Heroku / Railway.
    -   Database/Auth: Supabase.

## 6. Data Model (Postgres)

-   `users`: Managed by Supabase Auth. Contains `id`, `email`, etc.
-   `interviews`:
    -   `id` (uuid, PK)
    -   `user_id` (uuid, FK to `auth.users`)
    -   `candidate_name` (text)
    -   `interview_date` (timestamp)
    -   `transcript_content` (text) / `transcript_storage_path` (text)
    -   `status` (text: 'uploaded', 'processing', 'evaluated', 'error')
    -   `created_at` (timestamp)
-   `evaluation_criteria` (Potentially seeded initially, user-defined later):
    -   `id` (uuid, PK)
    -   `topic` (text, e.g., 'Python', 'SQL', 'Communication')
    -   `description` (text)
    -   `is_active` (boolean)
-   `evaluation_results`:
    -   `id` (uuid, PK)
    -   `interview_id` (uuid, FK to `interviews`)
    -   `criterion_id` (uuid, FK to `evaluation_criteria`)
    -   `score` (integer or float)
    -   `justification` (text)
    -   `supporting_quotes` (jsonb or text[])
    -   `created_at` (timestamp)
-   `evaluation_summaries`:
    -   `id` (uuid, PK)
    -   `interview_id` (uuid, FK to `interviews`, UNIQUE)
    -   `overall_score` (integer or float, optional)
    -   `overall_feedback` (text)
    -   `strengths` (text)
    -   `weaknesses` (text)
    -   `created_at` (timestamp)

## 7. Non-Functional Requirements

-   **Security:** Secure handling of transcript data, authentication via Supabase Auth.
-   **Scalability:** Backend API should be stateless where possible. Consider asynchronous processing for long evaluations.
-   **Reliability:** Graceful error handling if parsing or LLM evaluation fails. Status updates for the user.
-   **Maintainability:** Follow code style guidelines, use type annotations, document code (especially the LangGraph agent).
-   **Usability:** Simple, intuitive interface for uploading and viewing results.

## 8. Open Questions

-   Specific LLM choice and associated costs?
-   How to best handle ambiguous Q&A segments in transcripts?
-   Initial set of predefined evaluation criteria?
-   Maximum transcript length/size?
-   Need for fine-tuning the LLM for evaluation?

## 9. Required References

-   `./sprint-1.md`
-   `./sprint-2.md`
-   `./sprint-3.md`
-   `./sprint-4.md`
-   `./sprint-5.md`

*Note: Sprint files will be created in the workspace root for now due to path restrictions.* 