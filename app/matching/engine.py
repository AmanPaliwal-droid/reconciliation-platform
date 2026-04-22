from datetime import timedelta
from sqlalchemy import and_, or_
from app.connection import get_session
from app.models import Invoice, CustomerStatement, ReconciliationResult

class MatchingEngine:
    def __init__(self):
        self.session = get_session()
    
    def run_reconciliation(self, date_tolerance_days=7):
        """Main reconciliation process"""
        print("=" * 50)
        print("Step 3: Running Reconciliation Engine")
        print("=" * 50)
        
        # Get all pending invoices
        invoices = self.session.query(Invoice).filter_by(status='pending_reconciliation').all()
        print(f"\n📊 Found {len(invoices)} invoices to reconcile")
        
        matched_count = 0
        mismatch_count = 0
        unmatched_count = 0
        
        for invoice in invoices:
            result = self._match_invoice(invoice, date_tolerance_days)
            
            if result['match_status'] == 'exact':
                matched_count += 1
            elif result['match_status'] == 'partial':
                mismatch_count += 1
            else:
                unmatched_count += 1
            
            self._save_result(invoice.id, result)
        
        print(f"\n📊 Reconciliation Summary:")
        print(f"   ✅ Exact matches: {matched_count}")
        print(f"   ⚠️  Partial matches (mismatches): {mismatch_count}")
        print(f"   ❌ Unmatched: {unmatched_count}")
        
        return {
            'total': len(invoices),
            'exact_matches': matched_count,
            'partial_matches': mismatch_count,
            'unmatched': unmatched_count
        }
    
    def _match_invoice(self, invoice, date_tolerance_days):
        """Match a single invoice with customer statements"""
        
        # Find potential matches from customer statements
        potential_matches = self.session.query(CustomerStatement).filter(
            CustomerStatement.customer_code == invoice.customer_code
        ).all()
        
        best_match = None
        match_type = None
        
        for stmt in potential_matches:
            # Rule 1: Exact reference number match
            if stmt.reference_number == invoice.invoice_number:
                best_match = stmt
                match_type = 'exact_ref'
                break
            
            # Rule 2: Amount match within date range
            date_diff = abs((stmt.transaction_date - invoice.invoice_date).days)
            if abs(stmt.amount) == invoice.amount and date_diff <= date_tolerance_days:
                best_match = stmt
                match_type = 'amount_date'
                break
            
            # Rule 3: Fuzzy match (reference contains invoice number)
            if invoice.invoice_number in stmt.reference_number or stmt.reference_number in invoice.invoice_number:
                best_match = stmt
                match_type = 'fuzzy_ref'
                break
        
        if not best_match:
            return self._create_unmatched_result(invoice)
        
        # Check for mismatches
        return self._analyze_match(invoice, best_match, match_type)
    
    def _analyze_match(self, invoice, stmt, match_type):
        """Analyze if matched record has discrepancies"""
        
        mismatches = []
        amount_diff = invoice.amount - abs(stmt.amount)
        
        # Check amount mismatch
        if amount_diff != 0:
            mismatches.append({
                'type': 'price_mismatch',
                'marico_value': invoice.amount,
                'customer_value': abs(stmt.amount),
                'difference': amount_diff
            })
        
        # Check quantity mismatch
        if invoice.quantity and stmt.amount:
            # Approximate quantity check (customer statements often don't have quantity)
            estimated_qty = abs(stmt.amount) / (invoice.amount / invoice.quantity) if invoice.quantity else None
            if estimated_qty and abs(estimated_qty - invoice.quantity) > 1:
                mismatches.append({
                    'type': 'quantity_mismatch',
                    'marico_value': invoice.quantity,
                    'customer_value': estimated_qty,
                    'difference': invoice.quantity - estimated_qty
                })
        
        # Determine match status
        if len(mismatches) == 0:
            match_status = 'exact'
            severity = 'low'
            auto_resolvable = 1
        else:
            match_status = 'partial'
            # Determine severity based on mismatch size
            if abs(amount_diff) > 10000:
                severity = 'high'
                auto_resolvable = 0
            elif abs(amount_diff) > 1000:
                severity = 'medium'
                auto_resolvable = 0
            else:
                severity = 'low'
                auto_resolvable = 1
        
        return {
            'match_status': match_status,
            'customer_reference': stmt.reference_number,
            'marico_amount': invoice.amount,
            'customer_amount': abs(stmt.amount),
            'amount_difference': amount_diff,
            'quantity_difference': mismatches[0].get('difference') if mismatches else 0,
            'mismatch_type': mismatches[0]['type'] if mismatches else None,
            'severity': severity,
            'auto_resolvable': auto_resolvable,
            'resolution_status': 'open'
        }
    
    def _create_unmatched_result(self, invoice):
        """Create result for invoice with no customer match"""
        return {
            'match_status': 'unmatched',
            'customer_reference': None,
            'marico_amount': invoice.amount,
            'customer_amount': 0,
            'amount_difference': invoice.amount,
            'quantity_difference': 0,
            'mismatch_type': 'missing_in_customer_book',
            'severity': 'high',
            'auto_resolvable': 0,
            'resolution_status': 'escalated'
        }
    
    def _save_result(self, invoice_id, result):
        """Save reconciliation result to database"""
        
        # Check if result already exists
        existing = self.session.query(ReconciliationResult).filter_by(
            invoice_id=invoice_id
        ).first()
        
        if existing:
            # Update existing
            for key, value in result.items():
                setattr(existing, key, value)
        else:
            # Create new
            rec_result = ReconciliationResult(
                invoice_id=invoice_id,
                invoice_number=self.session.query(Invoice).get(invoice_id).invoice_number,
                customer_code=self.session.query(Invoice).get(invoice_id).customer_code,
                **result
            )
            self.session.add(rec_result)
        
        # Update invoice status
        invoice = self.session.query(Invoice).get(invoice_id)
        if result['match_status'] == 'exact':
            invoice.status = 'matched'
        elif result['match_status'] == 'partial':
            invoice.status = 'disputed'
        else:
            invoice.status = 'disputed'
        
        self.session.commit()
    
    def close(self):
        self.session.close()