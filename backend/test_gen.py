import os
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

from app.db import SessionLocal
from app.assessments import classify
from app.providers import generate

def test():
    with SessionLocal() as db:
        answers = {
            'use':'therapeutic', 
            'reference':'yes', 
            'exact':'yes', 
            'dosage_form':'classical_oral', 
            'claims_detail':'schedule_k', 
            'cross_border':'india_only', 
            'gmp_compliance':'schedule_t',
            'route':'oral',
            'origin':'plant'
        }
        result = classify(db, answers, 'en')
        prompt = (
            "You are an AYUSH regulatory JSON formatter. "
            "I will provide a JSON object in the user message. Your task is to output the EXACT SAME JSON object, "
            "but you must rewrite the paragraphs inside the 'posture' object and 'limitations' array to make them sound more professional, authoritative, and structured. "
            "Do NOT add, remove, or rename any keys in the root object. Return ONLY valid JSON."
        )
        
        try:
            formatted_result = generate(prompt, result)
            print("Successfully formatted.")
            print(json.dumps(formatted_result, indent=2))
        except Exception as e:
            print(f"FAILED: {e}")

if __name__ == "__main__":
    test()
