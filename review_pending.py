from app.matching.review_workflow import ReviewWorkflow

def manual_review_session():
    print("\n" + "=" * 60)
    print("MANUAL REVIEW WORKFLOW")
    print("=" * 60)
    
    workflow = ReviewWorkflow()
    
    # Show pending items
    pending = workflow.get_pending_reviews()
    
    if not pending:
        print("\n✅ No pending reviews! All resolved.")
        workflow.close()
        return
    
    print("\n" + "-" * 60)
    print("ACTIONS:")
    print("   Enter invoice number to resolve")
    print("   Type 'exit' to quit")
    print("-" * 60)
    
    while True:
        invoice = input("\n📋 Invoice number to resolve (or 'exit'): ").strip()
        
        if invoice.lower() == 'exit':
            break
        
        print("\n   Resolution options:")
        print("      1. accept - Accept customer's version")
        print("      2. reject - Reject and maintain Marico version")
        print("      3. adjust - Create adjustment for difference")
        
        action = input("   Action: ").strip()
        
        if action not in ['accept', 'reject', 'adjust']:
            print("   ❌ Invalid action. Use: accept, reject, or adjust")
            continue
        
        notes = input("   Resolution notes: ").strip()
        
        workflow.resolve_manually(invoice, action, notes)
        
        another = input("\n   Resolve another? (yes/no): ").strip()
        if another.lower() != 'yes':
            break
    
    workflow.close()
    print("\n✅ Manual review session complete!")

if __name__ == "__main__":
    manual_review_session()