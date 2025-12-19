import os
import glob
import json
from collections import defaultdict

def calculate_metrics(possible, predicted):
    """Calculates Precision, Recall, and F1 Score."""
    if not possible and not predicted:
        return 1.0, 1.0, 1.0
    
    tp = len(possible.intersection(predicted))
    fp = len(predicted - possible)
    fn = len(possible - predicted)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return precision, recall, f1

def calculate_jaccard_score(set1, set2):
    """Calculates Jaccard Index (Intersection over Union)."""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

def evaluate_results():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    # results_dir = os.path.join(SCRIPT_DIR, "test_results/2")
    results_dir = os.path.join(SCRIPT_DIR, "test_results_gemini_2.5_flash/2")
    
    if not os.path.exists(results_dir):
        print(f"Results directory '{results_dir}' not found.")
        return

    result_files = glob.glob(os.path.join(results_dir, "*.json"))
    
    if not result_files:
        print("No result files found.")
        return

    total_correct = 0 # Exact matches
    total_partial_score = 0.0 # Sum of Jaccard scores
    total_precision = 0.0
    total_recall = 0.0
    total_f1 = 0.0
    total_samples = 0
    
    # Store accuracy by relationship type
    relationship_stats = defaultdict(lambda: {
        "correct": 0, 
        "partial_sum": 0.0, 
        "precision_sum": 0.0,
        "recall_sum": 0.0,
        "f1_sum": 0.0,
        "total": 0
    })
    
    # Store accuracy by complexity
    complexity_stats = defaultdict(lambda: {
        "correct": 0, 
        "partial_sum": 0.0, 
        "precision_sum": 0.0,
        "recall_sum": 0.0,
        "f1_sum": 0.0,
        "total": 0
    })

    for file_path in result_files:
        filename = os.path.basename(file_path)
        complexity = filename.split('_')[0] if '_' in filename else "Unknown"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                results = json.load(f)
            except json.JSONDecodeError:
                print(f"Error decoding JSON in {filename}")
                continue
                
            for case in results:
                rel_type = case.get('relationship_type', 'UNKNOWN')
                possible_answers = set(case.get('possible_person_a', []))
                prediction_str = case.get('llm_prediction', '').strip()
                
                # Attempt to parse CSV string
                predicted_answers = set()
                
                # Check for "NOT_FOUND" or empty
                if "NOT_FOUND" in prediction_str:
                    pass # predicted_answers remains empty
                elif not prediction_str:
                    pass
                else:
                    # Clean up potential markdown code blocks if present
                    if "```" in prediction_str:
                        prediction_str = prediction_str.replace("```", "").strip()
                    
                    # Split by comma
                    parts = [p.strip() for p in prediction_str.split(',')]
                    # Filter out empty strings
                    parts = [p for p in parts if p]
                    predicted_answers = set(parts)
                
                # Evaluation: Exact Set Match
                is_correct = (possible_answers == predicted_answers)
                
                # Evaluation: Partial Score (Jaccard)
                partial_score = calculate_jaccard_score(possible_answers, predicted_answers)
                
                # Evaluation: Precision, Recall, F1
                precision, recall, f1 = calculate_metrics(possible_answers, predicted_answers)

                if is_correct:
                    total_correct += 1
                    relationship_stats[rel_type]["correct"] += 1
                    complexity_stats[complexity]["correct"] += 1
                
                total_partial_score += partial_score
                total_precision += precision
                total_recall += recall
                total_f1 += f1
                
                relationship_stats[rel_type]["partial_sum"] += partial_score
                relationship_stats[rel_type]["precision_sum"] += precision
                relationship_stats[rel_type]["recall_sum"] += recall
                relationship_stats[rel_type]["f1_sum"] += f1
                
                complexity_stats[complexity]["partial_sum"] += partial_score
                complexity_stats[complexity]["precision_sum"] += precision
                complexity_stats[complexity]["recall_sum"] += recall
                complexity_stats[complexity]["f1_sum"] += f1
                
                relationship_stats[rel_type]["total"] += 1
                complexity_stats[complexity]["total"] += 1
                total_samples += 1

    if total_samples == 0:
        print("No samples found to evaluate.")
        return

    overall_exact_accuracy = (total_correct / total_samples) * 100
    overall_avg_partial_score = (total_partial_score / total_samples) * 100
    overall_avg_precision = (total_precision / total_samples) * 100
    overall_avg_recall = (total_recall / total_samples) * 100
    overall_avg_f1 = (total_f1 / total_samples) * 100
    
    print("="*100)
    print(f"EVALUATION REPORT (Reverse Lookup)")
    print("="*100)
    print(f"Total Samples: {total_samples}")
    print(f"Total Exact Correct: {total_correct}")
    print(f"Overall Exact Accuracy: {overall_exact_accuracy:.2f}%")
    print(f"Overall Jaccard Index: {overall_avg_partial_score:.2f}%")
    print(f"Overall Precision:     {overall_avg_precision:.2f}%")
    print(f"Overall Recall:        {overall_avg_recall:.2f}%")
    print(f"Overall F1 Score:      {overall_avg_f1:.2f}%")
    print("-" * 100)
    
    print("\nAccuracy by Relationship Type:")
    print(f"{'Relationship':<20} | {'Jaccard':<8} | {'Precision':<10} | {'Recall':<10} | {'F1':<8} | {'Exact Match':<12} | {'Count':<10}")
    print("-" * 100)
    for rel, stats in sorted(relationship_stats.items()):
        total = stats['total']
        if total > 0:
            exact_acc = (stats['correct'] / total) * 100
            jaccard = (stats['partial_sum'] / total) * 100
            prec = (stats['precision_sum'] / total) * 100
            rec = (stats['recall_sum'] / total) * 100
            f1_score = (stats['f1_sum'] / total) * 100
        else:
            exact_acc = jaccard = prec = rec = f1_score = 0
            
        print(f"{rel:<20} | {jaccard:6.2f}%  | {prec:8.2f}%  | {rec:8.2f}%  | {f1_score:6.2f}%  | {exact_acc:6.2f}%      | {stats['correct']}/{total}")

    print("-" * 100)
    print("\nAccuracy by Complexity (Family Tree Depth):")
    print(f"{'Complexity':<10} | {'Jaccard':<8} | {'Precision':<10} | {'Recall':<10} | {'F1':<8} | {'Exact Match':<12} | {'Count':<10}")
    print("-" * 100)
    for comp, stats in sorted(complexity_stats.items()):
        total = stats['total']
        if total > 0:
            exact_acc = (stats['correct'] / total) * 100
            jaccard = (stats['partial_sum'] / total) * 100
            prec = (stats['precision_sum'] / total) * 100
            rec = (stats['recall_sum'] / total) * 100
            f1_score = (stats['f1_sum'] / total) * 100
        else:
            exact_acc = jaccard = prec = rec = f1_score = 0
            
        print(f"{comp:<10} | {jaccard:6.2f}%  | {prec:8.2f}%  | {rec:8.2f}%  | {f1_score:6.2f}%  | {exact_acc:6.2f}%      | {stats['correct']}/{total}")
    print("="*100)

if __name__ == "__main__":
    evaluate_results()
