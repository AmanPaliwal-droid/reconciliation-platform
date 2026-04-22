from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Invoice(Base):
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(50), nullable=False, unique=True)
    customer_code = Column(String(50), nullable=False)
    customer_name = Column(String(200))
    invoice_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    quantity = Column(Float)
    product_code = Column(String(50))
    pod_status = Column(String(20), default='pending')
    pod_url = Column(Text)
    status = Column(String(20), default='pending_reconciliation')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_inv_number', 'invoice_number'),
        Index('idx_inv_customer', 'customer_code'),
        Index('idx_inv_status', 'status'),
    )
    
    def __repr__(self):
        return f"<Invoice {self.invoice_number} ₹{self.amount}>"


class CustomerStatement(Base):
    __tablename__ = 'customer_statements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_code = Column(String(50), nullable=False)
    customer_name = Column(String(200))
    reference_number = Column(String(50), nullable=False)
    transaction_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(30))
    description = Column(Text)
    supporting_doc_url = Column(Text)
    ingested_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_cust_ref', 'customer_code', 'reference_number'),
        Index('idx_cust_date', 'transaction_date'),
    )
    
    def __repr__(self):
        return f"<CustomerStatement {self.reference_number} ₹{self.amount}>"


class ReconciliationResult(Base):
    __tablename__ = 'reconciliation_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    invoice_number = Column(String(50), nullable=False)
    customer_code = Column(String(50), nullable=False)
    match_status = Column(String(20))
    customer_reference = Column(String(50))
    marico_amount = Column(Float)
    customer_amount = Column(Float)
    amount_difference = Column(Float)
    quantity_difference = Column(Float)
    mismatch_type = Column(String(50))
    severity = Column(String(20))
    auto_resolvable = Column(Integer, default=0)
    resolution_status = Column(String(20), default='open')
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_rec_match', 'match_status'),
        Index('idx_rec_resolution', 'resolution_status'),
        Index('idx_rec_customer', 'customer_code'),
    )
    
    def __repr__(self):
        return f"<ReconciliationResult {self.invoice_number} -> {self.match_status}>"


class Claim(Base):
    __tablename__ = 'claims'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_number = Column(String(50), nullable=False, unique=True)
    customer_code = Column(String(50), nullable=False)
    customer_name = Column(String(200))
    invoice_reference = Column(String(50))
    reconciliation_result_id = Column(Integer, ForeignKey('reconciliation_results.id'))
    claim_type = Column(String(30))
    claimed_amount = Column(Float, nullable=False)
    approved_amount = Column(Float)
    status = Column(String(20), default='submitted')
    evidence_notes = Column(Text)
    evidence_urls = Column(Text)
    submitted_at = Column(DateTime, default=func.now())
    assigned_to = Column(String(100))
    reviewed_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_claim_number', 'claim_number'),
        Index('idx_claim_status', 'status'),
        Index('idx_claim_customer', 'customer_code'),
    )
    
    def __repr__(self):
        return f"<Claim {self.claim_number} ₹{self.claimed_amount} ({self.status})>"