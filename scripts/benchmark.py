import os
import json
import time
from typing import List, Dict
try:
    import pandas as pd
except ImportError:
    pd = None

from engines.pre_purchase_engine import PrePurchaseEngine
from services.pdf_extractor_robust import RobustPDFExtractor
from llm.model_loader import ModelLoader

def run_benchmark(ground_truth_path: str, data_dir: str):
    """
    Runs the CareBridge AI analysis pipeline against a ground truth dataset.
    Generates a performance report with validation and classification metrics.
    """
    print("🚀 Initializing Benchmark Engine...")
    
    # 1. Setup Models & Engines
    try:
        loader = ModelLoader()
        model, tokenizer = loader.get_model()
        engine = PrePurchaseEngine(model, tokenizer)
        extractor = RobustPDFExtractor(enable_ocr=True)
    except Exception as e:
        print(f"❌ Failed to initialize engines: {e}")
        return

    # 2. Load Ground Truth
    if not os.path.exists(ground_truth_path):
        print(f"❌ Ground truth file not found: {ground_truth_path}")
        return
        
    with open(ground_truth_path, 'r') as f:
        ground_truth = json.load(f)
        
    results = []
    
    # 3. Process Documents
    print(f"📋 Found {len(ground_truth)} test cases. Starting execution...")
    
    for entry in ground_truth:
        filename = entry['filename']
        pdf_path = os.path.join(data_dir, filename)
        
        if not os.path.exists(pdf_path):
            print(f"⚠️  Skipping {filename}: File not found in {data_dir}")
            continue
            
        print(f"🔍 [{filename}] Processing...")
        start_time = time.time()
        
        try:
            # Extract
            text, method = extractor.extract_text(pdf_path)
            
            # Analyze
            report = engine.run(text, provider_id="Other providers")
            
            # Metrics Calculation
            duration = time.time() - start_time
            
            # A document is "Valid" if it's a HEALTH_POLICY and passed validation
            actual_is_valid = (report.overall_policy_rating != "Weak" and "REJECTED" not in report.summary)
            expected_is_valid = entry.get('is_valid', False)
            
            results.append({
                "filename": filename,
                "expected_type": entry.get('document_type'),
                "actual_type": report.document_type,
                "type_match": (report.document_type == entry.get('document_type')),
                "is_valid_expected": expected_is_valid,
                "is_valid_actual": actual_is_valid,
                "validation_match": (actual_is_valid == expected_is_valid),
                "score": report.score_breakdown.adjusted_score,
                "confidence": report.validation_confidence,
                "duration": round(duration, 2),
                "extraction_method": method
            })
            print(f"✅ [{filename}] Done. Type: {report.document_type}, Score: {report.score_breakdown.adjusted_score}")
            
        except Exception as e:
            print(f"❌ [{filename}] Failed: {e}")
            results.append({
                "filename": filename,
                "error": str(e),
                "status": "FAILED"
            })
            
    # 4. Generate Summary Report
    if not results:
        print("📭 No results generated.")
        return

    print("\n" + "="*50)
    print("📊 CAREBRIDGE AI BENCHMARK SUMMARY")
    print("="*50)
    
    total = len(results)
    type_matches = sum(1 for r in results if r.get('type_match'))
    valid_matches = sum(1 for r in results if r.get('validation_match'))
    avg_duration = sum(r.get('duration', 0) for r in results) / total
    
    print(f"Total Test Cases:    {total}")
    print(f"Classification Acc:  {(type_matches/total)*100:.1f}%")
    print(f"Validation Acc:      {(valid_matches/total)*100:.1f}%")
    print(f"Avg Processing Time: {avg_duration:.2f}s")
    print("-" * 50)

    # 5. Save Results
    output_path = "evaluation/benchmark_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)
    
    if pd:
        csv_path = "evaluation/benchmark_results.csv"
        pd.DataFrame(results).to_csv(csv_path, index=False)
        print(f"💾 Detailed results saved to {csv_path}")
    else:
        print(f"💾 Detailed results saved to {output_path}")

if __name__ == "__main__":
    # Point to the testing directory by default
    run_benchmark("evaluation/ground_truth.json", "imp policies/testing")
