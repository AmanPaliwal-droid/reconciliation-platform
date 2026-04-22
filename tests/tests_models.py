import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.connection import get_session, init_db
from app.models import Invoice, CustomerStatement, ReconciliationResult, Claim

def test_create_invoice():
    session = get_session()
    
    invoice = Invoice(
        invoice_number="INV-TEST-001",
        customer_code="CUST001",
        customer_name="Test Customer",
        invoice_date="2026-01-15",
        amount=50000.00,
        quantity=100
    )
    session.add(invoice)
    session.commit()
    
    result = session.query(Invoice).filter_by(invoice_number="INV-TEST-001").first()
    assert result is not None
    print(f"✅ Invoice created: {result.invoice_number}")
    session.close()

def test_create_statement():
    session = get_session()
    
    stmt = CustomerStatement(
        customer_code="CUST001",
        customer_name="Test Customer",
        reference_number="INV-TEST-001",
        transaction_date="2026-01-20",
        amount=49800.00,
        transaction_type="invoice"
    )
    session.add(stmt)
    session.commit()
    
    result = session.query(CustomerStatement).filter_by(reference_number="INV-TEST-001").first()
    assert result is not None
    print(f"✅ Statement created: {result.reference_number}")
    session.close()

if __name__ == "__main__":
    print("=" * 50)
    print("Running Tests")
    print("=" * 50)
    
    init_db()
    test_create_invoice()
    test_create_statement()
    
    print("\n✅ All tests passed!")