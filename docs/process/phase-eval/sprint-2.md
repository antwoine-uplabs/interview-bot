<!-- LLM-CONTEXT-START -->
- **Document Type**: Sprint Plan
- **Applies To**: Interview Evaluator Application
- **Phase**: eval
- **Sprint**: 2
- **Audience**: Development Team
- **Status**: Completed
- **Latest Update**: 2025-04-17
<!-- LLM-CONTEXT-END -->

# Sprint 2: Core Evaluation Logic

**Goal**: Develop the core LangGraph agent structure, implement nodes for identifying Q&A pairs and performing basic evaluation with an LLM, and finalize the database schema in Supabase.

**Dates**: July 31, 2024 - August 14, 2024

## Completion Status

| Component                 | Status        | Estimated % | Actual % | Notes                                      |
| :------------------------ | :------------ | :---------- | :------- | :----------------------------------------- |
| LangGraph Agent Structure | Completed     | 30%         | 30%      | Full agent structure with all nodes       |
| Q&A Identification Node   | Completed     | 25%         | 25%      | Node implemented with transcript processor|
| Basic Evaluation Node     | Completed     | 25%         | 25%      | LLM-based evaluation with prompts         |
| LangSmith Integration     | Completed     | 10%         | 10%      | Added service layer with tracing          |
| API Integration           | Completed     | 5%          | 5%       | Added FastAPI endpoints                   |
| Supabase Schema Finalized | Completed     | 5%          | 5%       | All MVP tables created and seeded         |
| **Overall**               | **Completed** | **100%**    | **100%** | Core evaluation logic implemented         |

## Tasks

### Component: LangGraph Agent Structure
- [x] Define the overall state graph for the evaluation process (e.g., `ParsedTranscript`, `QAPairs`, `EvaluatedResults`, `ErrorReport`).
- [x] Implement the main LangGraph `Graph` or `StateMachine`.
- [x] Define stub functions for each node (e.g., `parse_transcript`, `extract_qa`, `evaluate_answers`, `generate_report`).
- [x] Define the edges and conditional logic connecting the nodes.
- [x] Set up basic configuration for the LLM to be used (e.g., API keys, model name).
- [x] Add LangSmith integration for tracing and monitoring.
- [x] Create documentation on LangSmith best practices.

### Component: Q&A Identification Node
- [x] Refine the LlamaIndex parsing logic from Sprint 1.
- [x] Use dialogue-aware semantic chunking for transcript processing.
- [x] Implement technical topic identification for extracted content.
- [x] Implement a LangGraph node that takes the parsed transcript text.
- [x] Define the Pydantic model for Q&A pairs (QAPair class).
- [x] Add extracted Q&A pairs to the agent's state.
- [x] Handle cases where no relevant Q&A pairs are found for a topic.
- [x] Use LlamaIndex's structured output capabilities to enhance extraction.

### Component: Basic Evaluation Node
- [x] Define a Pydantic model or schema for the evaluation output (CriterionEvaluation class).
- [x] Create detailed evaluation prompts for various technical areas.
- [x] Implement scoring guidelines for consistent evaluation.
- [x] Implement a LangGraph node that takes a Q&A pair and a relevant criterion.
- [x] Call the LLM and parse its response into the defined evaluation schema.
- [x] Add the evaluation result to the agent's state.
- [x] Handle potential LLM errors or unparseable responses.

### Component: LangSmith Integration
- [x] Create a LangSmith service class for integration.
- [x] Add environment variables for LangSmith configuration.
- [x] Create comprehensive documentation on LangSmith best practices.
- [x] Design evaluation strategy for interview assessment.
- [x] Implement tracing in FastAPI endpoints.
- [x] Add agent tracing and monitoring infrastructure.
- [x] Set up feedback collection mechanism.

### Component: API Integration
- [x] Create evaluation service to handle agent invocation.
- [x] Add new /evaluate endpoint for direct evaluation.
- [x] Update /upload endpoint with background processing.
- [x] Implement proper error handling for API calls.
- [x] Integrate LangSmith tracing in API endpoints.

### Component: Supabase Schema Finalized
- [x] Review and refine the initial schema from Sprint 1.
- [x] Define SQL scripts to create all tables required for MVP (users, interviews, evaluation_criteria, evaluation_results, evaluation_summaries) as per PRD.
- [x] Include appropriate data types, constraints, foreign keys, and indexes.
- [x] Seed the `evaluation_criteria` table with the initial predefined criteria for MVP.
- [x] Apply the schema to the Supabase project.

## Required References

-   `@interview_evaluator_prd.md`
-   `@docs/process/phase-eval/sprint-1.md`
-   `@docs/guides/langgraph_langsmith_guide.md`
-   `@docs/process/phase-eval/chunking_strategy.md`
-   [LangGraph Documentation](https://python.langchain.com/docs/langgraph/)
-   [LlamaIndex Structured Output](https://docs.llamaindex.ai/en/stable/module_guides/querying/structured_outputs/)
-   [LangSmith Documentation](https://docs.smith.langchain.com/)
-   [Supabase Schema Management](https://supabase.com/docs/guides/database/tables)

## Notes

- The evaluation logic in this sprint is basic. Focus on the flow and integration.
- Error handling for LLM calls is crucial.
- Ensure the agent state correctly accumulates data through the workflow.
- LangSmith integration provides monitoring and tracing capabilities.
- Dialogue-aware semantic chunking from Sprint 1 forms the foundation for our extraction.
- The evaluation strategy focuses on specific technical skills with standardized rubrics. 