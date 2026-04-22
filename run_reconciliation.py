from app.matching.engine import MatchingEngine
from app.matching.classifier import MismatchClassifier
from app.matching.auto_resolver import AutoResolver
from app.matching.review_workflow import ReviewWorkflow

def run_full_reconciliation():
    print("\n" + "=" * 60)
    print("MARICO RECONCILIATION PLATFORM - FULL RUN")
    print("=" * 60)
    
    # Step 1: Run matching engine
    print("\n📌 STEP 1: Running Matching Engine")
    engine = MatchingEngine()
    results = engine.run_reconciliation(date_tolerance_days=7)
    engine.close()
    
    # Step 2: Classify mismatches
    print("\n📌 STEP 2: Classifying Mismatches")
    classifier = MismatchClassifier()
    classifier.classify_all_mismatches()
    classifier.get_summary()
    classifier.close()
    
    # Step 3: Auto-resolution
    print("\n📌 STEP 3: Running Auto-Resolution")
    resolver = AutoResolver()
    resolution_results = resolver.run_auto_resolution()
    resolver.close()
    
    # Step 4: Show pending reviews
    print("\n📌 STEP 4: Pending Manual Reviews")
    workflow = ReviewWorkflow()
    pending = workflow.get_pending_reviews()
    workflow.close()
    
    print("\n" + "=" * 60)
    print("✅ Reconciliation process complete!")
    print(f"   Auto-resolved: {resolution_results['auto_resolved']}")
    print(f"   Manual review needed: {resolution_results['escalated']}")
    print("=" * 60)

if __name__ == "__main__":
    run_full_reconciliation()