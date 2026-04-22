from app.connection import get_session
from app.models import ReconciliationResult

class MismatchClassifier:
    def __init__(self):
        self.session = get_session()
    
    def classify_all_mismatches(self):
        """Classify all partial matches with detailed types"""
        
        mismatches = self.session.query(ReconciliationResult).filter_by(
            match_status='partial'
        ).all()
        
        print(f"\n🔍 Classifying {len(mismatches)} mismatches...")
        
        classified_count = 0
        for mismatch in mismatches:
            self._classify_single(mismatch)
            classified_count += 1
        
        print(f"✅ Classified {classified_count} mismatches")
        return classified_count
    
    def _classify_single(self, mismatch):
        """Classify a single mismatch with detailed type"""
        
        # Price mismatch classification
        if mismatch.mismatch_type == 'price_mismatch':
            diff_pct = abs(mismatch.amount_difference / mismatch.marico_amount * 100)
            
            if diff_pct <= 2:
                mismatch.sub_type = 'small_price_diff'
                mismatch.resolution_suggestion = 'auto_approve'
            elif diff_pct <= 10:
                mismatch.sub_type = 'medium_price_diff'
                mismatch.resolution_suggestion = 'review_pricing_agreement'
            else:
                mismatch.sub_type = 'large_price_diff'
                mismatch.resolution_suggestion = 'escalate_to_sales'
        
        # Check if claim exists
        if mismatch.customer_reference and 'CLM' in mismatch.customer_reference:
            mismatch.mismatch_type = 'claim_dispute'
            mismatch.sub_type = 'customer_claim'
            mismatch.resolution_suggestion = 'verify_claim_documentation'
        
        # Update based on amount difference direction
        if mismatch.amount_difference > 0:
            mismatch.direction = 'marico_higher'
        else:
            mismatch.direction = 'customer_higher'
        
        self.session.commit()
    
    def get_summary(self):
        """Get summary of all mismatches by type"""
        
        from sqlalchemy import func
        
        summary = self.session.query(
            ReconciliationResult.mismatch_type,
            func.count(ReconciliationResult.id).label('count'),
            func.sum(ReconciliationResult.amount_difference).label('total_diff')
        ).filter(
            ReconciliationResult.match_status == 'partial'
        ).group_by(
            ReconciliationResult.mismatch_type
        ).all()
        
        print("\n📊 Mismatch Summary:")
        print("-" * 50)
        for row in summary:
            print(f"   {row.mismatch_type}: {row.count} cases, ₹{abs(row.total_diff):,.2f} total difference")
        
        return summary
    
    def close(self):
        self.session.close()