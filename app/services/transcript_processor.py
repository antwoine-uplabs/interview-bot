import logging
from typing import Optional, Dict, Any, Tuple, List

# Import LlamaIndex related libraries (commented out for now)
# from llama_index import SimpleDirectoryReader, Document
# from llama_index.node_parser import SentenceSplitter

logger = logging.getLogger(__name__)

class TranscriptProcessor:
    """
    Service for processing interview transcripts using LlamaIndex
    
    This implementation follows the Dialogue-Aware Semantic Chunking approach
    described in chunking_strategy.md. For Sprint 1, we use a simplified version
    that will be enhanced in future sprints with LlamaIndex integration.
    """
    
    def __init__(self):
        """Initialize the transcript processor"""
        logger.info("Initializing TranscriptProcessor")
        # Placeholder for LlamaIndex setup
        # TODO: Add LlamaIndex and embedding model initialization in Sprint 2
        
    def process_transcript(self, file_path: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Process a transcript file and extract Q&A pairs with metadata
        
        Using a dialogue-aware chunking approach that preserves the natural
        structure of interview conversations.
        
        Returns:
            Tuple containing:
            - Success status (bool)
            - Processed data if successful, None otherwise
            - Error message if failed, None otherwise
        """
        try:
            logger.info(f"Processing transcript: {file_path}")
            
            # Read file with encoding fallback
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            # Parse the transcript into Q&A pairs
            qa_pairs = self._extract_qa_pairs(content)
            
            # Extract technical topics from each Q&A pair
            enriched_qa_pairs = self._enrich_with_metadata(qa_pairs)
            
            # Identify technical areas covered in the interview
            technical_areas = self._identify_technical_areas(enriched_qa_pairs)
            
            # For Sprint 1, return a structured result
            result = {
                "success": True,
                "transcript_length": len(content),
                "num_exchanges": len(enriched_qa_pairs),
                "technical_areas": technical_areas,
                "qa_pairs": enriched_qa_pairs[:5],  # Just first 5 for brevity in API response
                "all_qa_pairs": enriched_qa_pairs,  # Store complete data for evaluation
                "note": "Using dialogue-aware semantic chunking"
            }
            
            logger.info(f"Processed transcript with {len(enriched_qa_pairs)} Q&A pairs")
            return True, result, None
            
        except Exception as e:
            logger.error(f"Error processing transcript: {e}", exc_info=True)
            return False, None, f"Error processing transcript: {str(e)}"
    
    def _extract_qa_pairs(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract question-answer pairs from the transcript
        
        This implements our primary chunking strategy of using Q&A pairs as the
        basic semantic unit for interview analysis.
        """
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        qa_pairs = []
        current_pair = {"question": "", "answer": "", "context": ""}
        current_speaker = None
        in_question = False
        in_answer = False
        
        for line in lines:
            if line.startswith("Interviewer:") or line.startswith("I:"):
                # New interviewer question - finalize previous pair if exists
                if in_answer and current_pair["question"] and current_pair["answer"]:
                    qa_pairs.append(current_pair.copy())
                
                # Start new pair
                current_speaker = "Interviewer"
                in_question = True
                in_answer = False
                
                # Extract question text
                question_text = line.split(":", 1)[1].strip() if ":" in line else line.strip()
                
                # If this is a follow-up question, include previous context
                if qa_pairs and question_text.lower().startswith(("could you", "can you", "would you", "what about")):
                    current_pair = {
                        "question": question_text,
                        "answer": "",
                        "context": qa_pairs[-1]["question"]  # Include previous question as context
                    }
                else:
                    current_pair = {"question": question_text, "answer": "", "context": ""}
                
            elif line.startswith("Candidate:") or line.startswith("C:"):
                # Candidate response
                current_speaker = "Candidate"
                in_question = False
                in_answer = True
                
                # Extract answer beginning
                current_pair["answer"] = line.split(":", 1)[1].strip() if ":" in line else line.strip()
                
            elif current_speaker:
                # Continuation of current speaker's text
                if in_question:
                    current_pair["question"] += " " + line
                elif in_answer:
                    current_pair["answer"] += " " + line
        
        # Add the final pair if it exists
        if in_answer and current_pair["question"] and current_pair["answer"]:
            qa_pairs.append(current_pair.copy())
            
        return qa_pairs
    
    def _enrich_with_metadata(self, qa_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich Q&A pairs with metadata for improved retrieval
        
        Adds technical topic identification and position metadata.
        """
        # Technical topic keywords to identify
        topic_keywords = {
            "Python": ["python", "pandas", "numpy", "dataframe", "list", "dict", "pip", "library"],
            "SQL": ["sql", "query", "database", "join", "table", "select", "from", "where", "group by"],
            "Statistics": ["statistics", "probability", "distribution", "hypothesis", "p-value", "confidence", "mean", "median"],
            "Machine Learning": ["machine learning", "model", "algorithm", "feature", "train", "test", "validation", "accuracy", "precision", "recall"],
            "Deep Learning": ["neural", "network", "deep learning", "cnn", "rnn", "lstm", "transformer"],
            "Data Engineering": ["data engineering", "pipeline", "etl", "spark", "hadoop", "data warehouse"],
            "Communication": ["explain", "communicate", "team", "stakeholder", "present", "non-technical"]
        }
        
        for i, pair in enumerate(qa_pairs):
            # Add position metadata
            pair["position"] = i + 1
            pair["position_percentage"] = (i + 1) / len(qa_pairs)
            
            # Identify technical topics
            combined_text = f"{pair['question']} {pair['answer']}".lower()
            pair["topics"] = []
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in combined_text for keyword in keywords):
                    pair["topics"].append(topic)
            
            # If no topics identified, mark as "General"
            if not pair["topics"]:
                pair["topics"].append("General")
                
            # Check for code examples (helps with retrieval of technical implementations)
            pair["contains_code"] = "```" in pair["answer"] or any(line.startswith("    ") for line in pair["answer"].split("\n"))
                
        return qa_pairs
    
    def _identify_technical_areas(self, qa_pairs: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Identify and count technical areas covered in the interview
        """
        area_counts = {}
        
        for pair in qa_pairs:
            for topic in pair["topics"]:
                if topic in area_counts:
                    area_counts[topic] += 1
                else:
                    area_counts[topic] = 1
                    
        return area_counts
    
    # Future methods (to be implemented in Sprint 2):
    # - extract_structured_knowledge
    # - build_llama_index
    # - evaluate_technical_skills


# Create a singleton instance
transcript_processor = TranscriptProcessor()