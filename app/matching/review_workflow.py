from app.connection import get_session
from app.models import ReconciliationResult, Claim

class ReviewWorkflow:
    def __init__(self):
        self.session = get_session()
    
    def get_pending_reviews(self):
        """Get all items pending manual review"""
        
        pending = self.session.query(ReconciliationResult).filter(
            ReconciliationResult.resolution_status.in_(['in_progress', 'escalated'])
        ).all()
        
        print("\n📋 Pending Manual Reviews:")
        print("-" * 60)
        
        for item in pending:
            claim = self.session.query(Claim).filter_by(
                reconciliation_result_id=item.id
            ).first()
            
            print(f"\n   Invoice: {item.invoice_number}")
            print(f"   Customer: {item.customer_code}")
            print(f"   Issue: {item.mismatch_type}")
            print(f"   Difference: ₹{abs(item.amount_difference):,.2f}")
            print(f"   Status: {item.resolution_status}")
            if claim:
                print(f"   Claim ID: {claim.claim_number}")
                print(f"   Claim Amount: ₹{claim.claimed_amount:,.2f}")
            print(f"   Suggested Action: {self._get_suggestion(item)}")
        
        return pending
    
    def _get_suggestion(self, mismatch):
        """Provide resolution suggestion based on mismatch type"""
        
        suggestions = {
            'price_mismatch': 'Verify pricing agreement with customer',
            'quantity_mismatch': 'Check delivery quantities against POD',
            'missing_in_customer_book': 'Resend invoice to customer for booking',
            'claim_dispute': 'Review customer claim documentation'
        }
        
        return suggestions.get(mismatch.mismatch_type, 'Manual review required')
    
    def resolve_manually(self, invoice_number, action, notes):
        """Manually resolve a reconciliation issue"""
        
        result = self.session.query(ReconciliationResult).filter_by(
            invoice_number=invoice_number
        ).first()
        
        if not result:
            print(f"❌ Invoice {invoice_number} not found")
            return False
        
        result.resolution_status = 'resolved'
        result.resolution_notes = f"Manual resolution: {action} - {notes}"
        result.resolved_at = datetime.now()
        
        # Update associated claim if exists
        claim = self.session.query(Claim).filter_by(
            reconciliation_result_id=result.id
        ).first()
        
        if claim:
            claim.status = 'approved' if 'accept' in action.lower() else 'rejected'
            claim.approved_amount = result.amount_difference if 'accept' in action.lower() else 0
            claim.resolved_at = datetime.now()
        
        self.session.commit()
        print(f"✅ Resolved {invoice_number}: {action}")
        return True
    
    def close(self):
        self.session.close()