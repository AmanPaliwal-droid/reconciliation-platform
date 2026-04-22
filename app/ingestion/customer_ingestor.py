from datetime import datetime
from app.connection import get_session
from app.models import CustomerStatement

class CustomerIngestor:
    def __init__(self):
        self.session = get_session()
    
    def ingest_from_dict(self, statement_data: dict):
        """Ingest a single customer statement transaction"""
        statement = CustomerStatement(
            customer_code=statement_data['customer_code'],
            customer_name=statement_data.get('customer_name', ''),
            reference_number=statement_data['reference_number'],
            transaction_date=statement_data['transaction_date'],
            amount=statement_data['amount'],
            transaction_type=statement_data.get('transaction_type', 'invoice'),
            description=statement_data.get('description', ''),
            supporting_doc_url=statement_data.get('supporting_doc_url')
        )
        
        self.session.add(statement)
        self.session.commit()
        print(f"✅ Ingested statement: {statement.reference_number} for {statement.customer_code}")
        return statement
    
    def ingest_from_csv(self, csv_path: str):
        """Ingest multiple customer statements from CSV"""
        import csv
        
        statements_ingested = 0
        errors = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    statement_data = {
                        'customer_code': row['customer_code'],
                        'customer_name': row.get('customer_name', ''),
                        'reference_number': row['reference_number'],
                        'transaction_date': datetime.strptime(row['transaction_date'], '%Y-%m-%d').date(),
                        'amount': float(row['amount']),
                        'transaction_type': row.get('transaction_type', 'invoice'),
                        'description': row.get('description', ''),
                    }
                    self.ingest_from_dict(statement_data)
                    statements_ingested += 1
                except Exception as e:
                    errors.append(f"Row {row}: {e}")
        
        print(f"\n📊 Summary: {statements_ingested} statements ingested, {len(errors)} errors")
        return statements_ingested
    
    def close(self):
        self.session.close()