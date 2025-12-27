import os
import glob
import csv
from collections import defaultdict

def evaluate_results():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(SCRIPT_DIR, "test_results_gemini_3_flash/1")
    
    if not os.path.exists(results_dir):
        print(f"Results directory '{results_dir}' not found.")
        return

    result_files = glob.glob(os.path.join(results_dir, "*.csv"))
    
    if not result_files:
        print("No result files found.")
        return

    total_correct = 0
    total_samples = 0
    
    # Store accuracy by relationship type
    relationship_stats = defaultdict(lambda: {"correct": 0, "total": 0})
    
    # Store accuracy by complexities (folder name G4, G5 etc - inferred from filename)
    complexity_stats = defaultdict(lambda: {"correct": 0, "total": 0})

    for file_path in result_files:
        filename = os.path.basename(file_path)
        # Assuming filename format G{complexity}_N{nodes}.csv or similar
        complexity = filename.split('_')[0] if '_' in filename else "Unknown"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ground_truth = row.get('relationship_type', '').strip().upper()
                prediction = row.get('llm_prediction', '').strip().upper()
                
                # Check for "Person A is Person B's [RELATIONSHIP]" pattern and extract relationship
                # Or assume the prompt instruction made it output ONLY the relationship.
                # The prompt said "return only the relationship", hopefully it obeyed.
                # But sometimes LLMs are chatty. Let's do a simple check.
                
                # If the prediction is inside a sentence, we might need more robust parsing.
                # For now, let's assume it's relatively clean or exact match.
                # We can refine this if we see failures.
                
                is_correct = ground_truth == prediction
                
                if is_correct:
                    total_correct += 1
                    relationship_stats[ground_truth]["correct"] += 1
                    complexity_stats[complexity]["correct"] += 1
                
                relationship_stats[ground_truth]["total"] += 1
                complexity_stats[complexity]["total"] += 1
                total_samples += 1

    if total_samples == 0:
        print("No samples found to evaluate.")
        return

    overall_accuracy = (total_correct / total_samples) * 100
    
    print("="*40)
    print(f"EVALUATION REPORT")
    print("="*40)
    print(f"Total Samples: {total_samples}")
    print(f"Total Correct: {total_correct}")
    print(f"Overall Accuracy: {overall_accuracy:.2f}%")
    print("-" * 40)
    
    print("\nAccuracy by Relationship Type:")
    print(f"{'Relationship':<20} | {'Accuracy':<10} | {'Count':<10}")
    print("-" * 46)
    for rel, stats in sorted(relationship_stats.items()):
        acc = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"{rel:<20} | {acc:6.2f}%    | {stats['total']}/{stats['total']}")

    print("-" * 40)
    print("\nAccuracy by Complexity (Family Tree Depth):")
    print(f"{'Complexity':<10} | {'Accuracy':<10} | {'Count':<10}")
    print("-" * 36)
    for comp, stats in sorted(complexity_stats.items()):
        acc = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"{comp:<10} | {acc:6.2f}%    | {stats['total']}/{stats['total']}")
    print("="*40)

if __name__ == "__main__":
    evaluate_results()
