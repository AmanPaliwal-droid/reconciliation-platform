from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.connection import get_session
from app.models import Invoice, CustomerStatement, ReconciliationResult, Claim

# Create FastAPI app
app = FastAPI(title="Marico Reconciliation API", version="1.0")

# Add CORS middleware - ADD THIS BLOCK
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Pydantic models for request/response
class ResolutionRequest(BaseModel):
    action: str  # accept, reject, adjust
    notes: str

class ClaimUpdateRequest(BaseModel):
    status: str  # approved, rejected, paid
    approved_amount: Optional[float] = None
    notes: Optional[str] = None

# Dependency to get DB session
def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()

# ==================== DASHBOARD ENDPOINTS ====================

@app.get("/api/dashboard/summary")
def get_summary(db: Session = Depends(get_db)):
    """Get dashboard KPIs"""
    
    total_invoices = db.query(Invoice).count()
    matched = db.query(ReconciliationResult).filter_by(match_status='exact').count()
    mismatched = db.query(ReconciliationResult).filter_by(match_status='partial').count()
    unresolved = db.query(ReconciliationResult).filter(
        ReconciliationResult.resolution_status.in_(['open', 'in_progress', 'escalated'])
    ).count()
    
    # Calculate blocked working capital
    blocked_capital = db.query(ReconciliationResult).filter(
        ReconciliationResult.resolution_status != 'resolved'
    ).with_entities(
        ReconciliationResult.amount_difference
    ).all()
    
    total_blocked = sum([abs(r[0]) for r in blocked_capital if r[0] and r[0] > 0])
    
    # Get ageing data
    ageing = db.query(ReconciliationResult).filter(
        ReconciliationResult.match_status == 'partial',
        ReconciliationResult.created_at < datetime.now() - timedelta(days=7)
    ).count()
    
    return {
        'total_invoices': total_invoices,
        'matched_count': matched,
        'mismatched_count': mismatched,
        'unresolved_count': unresolved,
        'blocked_working_capital': total_blocked,
        'aged_mismatches': ageing,
        'match_rate': round(matched / total_invoices * 100, 2) if total_invoices > 0 else 0
    }

@app.get("/api/dashboard/mismatches")
def get_mismatches(
    limit: int = 50,
    offset: int = 0,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of mismatches with optional filters"""
    
    query = db.query(ReconciliationResult).filter(
        ReconciliationResult.match_status == 'partial'
    )
    
    if severity:
        query = query.filter_by(severity=severity)
    
    results = query.order_by(
        ReconciliationResult.amount_difference.desc()
    ).offset(offset).limit(limit).all()
    
    mismatches = []
    for r in results:
        # Get associated claim if exists
        claim = db.query(Claim).filter_by(reconciliation_result_id=r.id).first()
        
        mismatches.append({
            'id': r.id,
            'invoice_number': r.invoice_number,
            'customer_code': r.customer_code,
            'match_status': r.match_status,
            'marico_amount': r.marico_amount,
            'customer_amount': r.customer_amount,
            'amount_difference': r.amount_difference,
            'mismatch_type': r.mismatch_type,
            'severity': r.severity,
            'resolution_status': r.resolution_status,
            'claim_id': claim.claim_number if claim else None,
            'created_at': r.created_at.isoformat() if r.created_at else None
        })
    
    return {
        'total': len(mismatches),
        'mismatches': mismatches
    }

@app.get("/api/dashboard/claims")
def get_claims(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all claims"""
    
    query = db.query(Claim)
    if status:
        query = query.filter_by(status=status)
    
    claims = query.order_by(Claim.submitted_at.desc()).all()
    
    return {
        'total': len(claims),
        'claims': [
            {
                'claim_number': c.claim_number,
                'customer_code': c.customer_code,
                'invoice_reference': c.invoice_reference,
                'claim_type': c.claim_type,
                'claimed_amount': c.claimed_amount,
                'approved_amount': c.approved_amount,
                'status': c.status,
                'submitted_at': c.submitted_at.isoformat() if c.submitted_at else None
            }
            for c in claims
        ]
    }

@app.get("/api/dashboard/customers")
def get_customer_summary(db: Session = Depends(get_db)):
    """Get customer-wise reconciliation summary"""
    
    from sqlalchemy import func
    
    summary = db.query(
        ReconciliationResult.customer_code,
        func.count(ReconciliationResult.id).label('total_transactions'),
        func.sum(func.abs(ReconciliationResult.amount_difference)).label('total_discrepancy')
    ).filter(
        ReconciliationResult.match_status == 'partial'
    ).group_by(
        ReconciliationResult.customer_code
    ).all()
    
    return {
        'customers': [
            {
                'customer_code': s[0],
                'total_transactions': s[1],
                'total_discrepancy': float(s[2]) if s[2] else 0
            }
            for s in summary
        ]
    }

# ==================== RESOLUTION ENDPOINTS ====================

@app.post("/api/resolve/{invoice_number}")
def resolve_mismatch(
    invoice_number: str,
    resolution: ResolutionRequest,
    db: Session = Depends(get_db)
):
    """Manually resolve a mismatch"""
    
    result = db.query(ReconciliationResult).filter_by(
        invoice_number=invoice_number
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    result.resolution_status = 'resolved'
    result.resolution_notes = f"Manual resolution: {resolution.action} - {resolution.notes}"
    result.resolved_at = datetime.now()
    
    # Update associated claim
    claim = db.query(Claim).filter_by(reconciliation_result_id=result.id).first()
    if claim:
        if resolution.action == 'accept':
            claim.status = 'approved'
            claim.approved_amount = abs(result.amount_difference)
        elif resolution.action == 'reject':
            claim.status = 'rejected'
            claim.approved_amount = 0
        else:
            claim.status = 'adjustment_created'
            claim.approved_amount = abs(result.amount_difference) / 2
        
        claim.resolved_at = datetime.now()
    
    db.commit()
    
    return {
        'status': 'success',
        'message': f'Invoice {invoice_number} resolved',
        'resolution': resolution.action
    }

@app.put("/api/claims/{claim_number}")
def update_claim(
    claim_number: str,
    update: ClaimUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update claim status"""
    
    claim = db.query(Claim).filter_by(claim_number=claim_number).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim.status = update.status
    if update.approved_amount:
        claim.approved_amount = update.approved_amount
    if update.notes:
        claim.evidence_notes = update.notes
    
    claim.reviewed_at = datetime.now()
    db.commit()
    
    return {
        'status': 'success',
        'claim_number': claim_number,
        'new_status': update.status
    }

# ==================== EXPORT ENDPOINTS ====================

@app.get("/api/export/reconciliation")
def export_reconciliation(db: Session = Depends(get_db)):
    """Export all reconciliation results"""
    
    results = db.query(ReconciliationResult).all()
    
    export_data = []
    for r in results:
        export_data.append({
            'invoice_number': r.invoice_number,
            'customer_code': r.customer_code,
            'match_status': r.match_status,
            'marico_amount': r.marico_amount,
            'customer_amount': r.customer_amount,
            'amount_difference': r.amount_difference,
            'mismatch_type': r.mismatch_type,
            'resolution_status': r.resolution_status
        })
    
    return {
        'export_date': datetime.now().isoformat(),
        'total_records': len(export_data),
        'data': export_data
    }

# ==================== HEALTH CHECK ====================

@app.get("/health")
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}