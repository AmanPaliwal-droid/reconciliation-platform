from datetime import datetime
from app.connection import get_session
from app.models import Invoice

class SAPIngestor:
    def __init__(self):
        self.session = get_session()
    
    def ingest_from_dict(self, invoice_data: dict):
        """Ingest a single invoice from dictionary"""
        invoice = Invoice(
            invoice_number=invoice_data['invoice_number'],
            customer_code=invoice_data['customer_code'],
            customer_name=invoice_data.get('customer_name', ''),
            invoice_date=invoice_data['invoice_date'],
            amount=invoice_data['amount'],
            quantity=invoice_data.get('quantity'),
            product_code=invoice_data.get('product_code'),
            pod_status=invoice_data.get('pod_status', 'pending'),
            pod_url=invoice_data.get('pod_url'),
            status='pending_reconciliation'
        )
        
        # Check if invoice already exists
        existing = self.session.query(Invoice).filter_by(
            invoice_number=invoice.invoice_number
        ).first()
        
        if existing:
            print(f"⚠️ Invoice {invoice.invoice_number} already exists, skipping")
            return None
        
        self.session.add(invoice)
        self.session.commit()
        print(f"✅ Ingested invoice: {invoice.invoice_number}")
        return invoice
    
    def ingest_from_csv(self, csv_path: str):
        """Ingest multiple invoices from CSV file"""
        import csv
        from datetime import datetime
        
        invoices_ingested = 0
        errors = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Map CSV columns to your schema
                    invoice_data = {
                        'invoice_number': row['invoice_number'],
                        'customer_code': row['customer_code'],
                        'customer_name': row.get('customer_name', ''),
                        'invoice_date': datetime.strptime(row['invoice_date'], '%Y-%m-%d').date(),
                        'amount': float(row['amount']),
                        'quantity': float(row['quantity']) if row.get('quantity') else None,
                        'product_code': row.get('product_code'),
                        'pod_status': row.get('pod_status', 'pending'),
                    }
                    self.ingest_from_dict(invoice_data)
                    invoices_ingested += 1
                except Exception as e:
                    errors.append(f"Row {row}: {e}")
        
        print(f"\n📊 Summary: {invoices_ingested} invoices ingested, {len(errors)} errors")
        return invoices_ingested
    
    def close(self):
        self.session.close()