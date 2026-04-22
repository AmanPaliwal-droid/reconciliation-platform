from datetime import datetime
from app.connection import get_session
from app.models import ReconciliationResult, Claim

class AutoResolver:
    def __init__(self):
        self.session = get_session()
        self.auto_resolved_count = 0
        self.escalated_count = 0
    
    def run_auto_resolution(self):
        """Automatically resolve eligible mismatches"""
        print("\n" + "=" * 50)
        print("Step 4: Auto-Resolution Engine")
        print("=" * 50)
        
        # Get all open mismatches
        open_mismatches = self.session.query(ReconciliationResult).filter(
            ReconciliationResult.match_status == 'partial',
            ReconciliationResult.resolution_status == 'open'
        ).all()
        
        print(f"\n📊 Found {len(open_mismatches)} open mismatches to review")
        
        for mismatch in open_mismatches:
            self._resolve_single(mismatch)
        
        print(f"\n📊 Auto-Resolution Summary:")
        print(f"   ✅ Auto-resolved: {self.auto_resolved_count}")
        print(f"   ⚠️  Escalated for review: {self.escalated_count}")
        
        self.session.commit()
        return {
            'auto_resolved': self.auto_resolved_count,
            'escalated': self.escalated_count
        }
    
    def _resolve_single(self, mismatch):
        """Resolve a single mismatch based on rules"""
        
        # Rule 1: Small price difference (< ₹500) - auto approve
        if mismatch.mismatch_type == 'price_mismatch' and abs(mismatch.amount_difference) < 500:
            mismatch.resolution_status = 'resolved'
            mismatch.resolution_notes = f"Auto-resolved: Small price difference of ₹{abs(mismatch.amount_difference)}"
            mismatch.resolved_at = datetime.now()
            self.auto_resolved_count += 1
            print(f"   ✅ Auto-resolved: {mismatch.invoice_number} (₹{abs(mismatch.amount_difference)} diff)")
            return
        
        # Rule 2: Customer higher amount (customer paid less) - create credit note request
        if mismatch.amount_difference > 0 and mismatch.mismatch_type == 'price_mismatch':
            self._create_claim(mismatch, 'price_protection', 
                               f"Customer paid ₹{abs(mismatch.amount_difference)} less than invoice")
            mismatch.resolution_status = 'in_progress'
            self.escalated_count += 1
            print(f"   ⚠️  Escalated: {mismatch.invoice_number} (Customer short payment ₹{abs(mismatch.amount_difference)})")
            return
        
        # Rule 3: Marico higher amount (customer paid more) - initiate refund
        if mismatch.amount_difference < 0 and mismatch.mismatch_type == 'price_mismatch':
            self._create_claim(mismatch, 'overpayment', 
                               f"Customer overpaid by ₹{abs(mismatch.amount_difference)}")
            mismatch.resolution_status = 'in_progress'
            self.escalated_count += 1
            print(f"   ⚠️  Escalated: {mismatch.invoice_number} (Customer overpaid ₹{abs(mismatch.amount_difference)})")
            return
        
        # Rule 4: Missing in customer book - escalate immediately
        if mismatch.mismatch_type == 'missing_in_customer_book':
            mismatch.resolution_status = 'escalated'
            mismatch.resolution_notes = "Invoice not found in customer records - requires follow-up"
            self.escalated_count += 1
            print(f"   🔴 Escalated: {mismatch.invoice_number} (Missing from customer books)")
            return
        
        # Default: escalate for manual review
        mismatch.resolution_status = 'escalated'
        self.escalated_count += 1
        print(f"   ⚠️  Escalated: {mismatch.invoice_number} (Requires manual review)")
    
    def _create_claim(self, mismatch, claim_type, description):
        """Create a claim record for escalated issues"""
        
        claim = Claim(
            claim_number=f"CLM-{datetime.now().strftime('%Y%m%d')}-{mismatch.id}",
            customer_code=mismatch.customer_code,
            invoice_reference=mismatch.invoice_number,
            reconciliation_result_id=mismatch.id,
            claim_type=claim_type,
            claimed_amount=abs(mismatch.amount_difference),
            status='submitted',
            evidence_notes=description,
            submitted_at=datetime.now()
        )
        
        self.session.add(claim)
    
    def close(self):
        self.session.close()