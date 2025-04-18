#!/usr/bin/env python3
"""
Command-line tool for processing and testing example interview documents
with the LangGraph agent.

This script allows you to process example documents from the interview-content
directory and test the interview evaluation LangGraph agent without going
through the web interface.
"""

import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("process_example")

# Import our evaluation services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.agents.evaluator import evaluator_agent, InterviewEvaluationState, EvaluationStatus
from app.services.transcript_processor import transcript_processor

async def process_document(file_path: str, output_file: Optional[str] = None) -> None:
    """Process a single document using the transcript processor."""
    
    # Extract candidate name from filename
    candidate_name = os.path.splitext(os.path.basename(file_path))[0]
    
    logger.info(f"Processing {file_path} for candidate {candidate_name}")
    
    try:
        # Process the transcript to extract Q&A pairs
        success, processed_data, error = transcript_processor.process_transcript(file_path)
        
        if not success or not processed_data:
            logger.error(f"Failed to process transcript: {error}")
            return
            
        qa_pairs = processed_data['all_qa_pairs']
        logger.info(f"Extracted {len(qa_pairs)} Q&A pairs from transcript")
        
        # Print out the extracted Q&A pairs
        print("\n===== TRANSCRIPT PROCESSING RESULTS =====")
        print(f"Candidate: {candidate_name}")
        print(f"File: {file_path}")
        print(f"Total Q&A Pairs: {len(qa_pairs)}")
        
        # Print technical areas summary
        print("\nTechnical Areas Detected:")
        for area, count in processed_data['technical_areas'].items():
            print(f"- {area}: {count} mentions")
        
        # Print each Q&A pair
        print("\nExtracted Q&A Pairs:")
        for i, qa in enumerate(qa_pairs):
            print(f"\n--- Pair {i+1} ---")
            print(f"Question: {qa['question']}")
            print(f"Answer: {qa['answer'][:100]}..." if len(qa['answer']) > 100 else f"Answer: {qa['answer']}")
            print(f"Topics: {', '.join(qa['topics'])}")
            print(f"Contains Code: {'Yes' if qa['contains_code'] else 'No'}")
        
        # Save to output file if specified
        if output_file:
            import json
            with open(output_file, 'w') as f:
                json.dump({
                    "candidate_name": candidate_name,
                    "file_processed": file_path,
                    "timestamp": datetime.now().isoformat(),
                    "technical_areas": processed_data['technical_areas'],
                    "qa_pairs": qa_pairs
                }, f, indent=2)
            logger.info(f"Processing results saved to {output_file}")
            
    except Exception as e:
        logger.exception(f"Error processing document: {e}")

async def process_directory(directory: str, output_dir: Optional[str] = None) -> None:
    """Process all supported files in a directory."""
    
    # Check if directory exists
    if not os.path.isdir(directory):
        logger.error(f"Directory not found: {directory}")
        return
        
    # Get all supported files
    supported_extensions = ['.txt', '.md']
    files = []
    
    for file in os.listdir(directory):
        if any(file.endswith(ext) for ext in supported_extensions):
            files.append(os.path.join(directory, file))
            
    if not files:
        logger.error(f"No supported files found in {directory}")
        return
        
    logger.info(f"Found {len(files)} files to process")
    
    # Create output directory if needed
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Process each file
    for file_path in files:
        output_file = None
        if output_dir:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_file = os.path.join(output_dir, f"{base_name}_evaluation.json")
            
        await process_document(file_path, output_file)

def print_usage():
    """Print usage instructions."""
    print("Usage:")
    print("  process_example.py file <file_path> [--output <output_file>]")
    print("  process_example.py dir <directory_path> [--output <output_directory>]")
    print()
    print("Examples:")
    print("  process_example.py file interview-content/scenario1.md")
    print("  process_example.py file interview-content/scenario1.md --output results/scenario1_eval.json")
    print("  process_example.py dir interview-content --output evaluation_results")

async def main():
    """Main function to parse arguments and run the appropriate command."""
    if len(sys.argv) < 3:
        print_usage()
        return
        
    command = sys.argv[1]
    path = sys.argv[2]
    
    output = None
    if "--output" in sys.argv:
        output_index = sys.argv.index("--output")
        if output_index + 1 < len(sys.argv):
            output = sys.argv[output_index + 1]
    
    if command == "file":
        await process_document(path, output)
    elif command == "dir":
        await process_directory(path, output)
    else:
        print(f"Unknown command: {command}")
        print_usage()

if __name__ == "__main__":
    asyncio.run(main())