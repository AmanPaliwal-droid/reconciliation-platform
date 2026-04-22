from app.ingestion.sap_ingestor import SAPIngestor
from app.ingestion.customer_ingestor import CustomerIngestor

def ingest_sample_data():
    print("=" * 50)
    print("Step 2: Data Ingestion")
    print("=" * 50)
    
    # Ingest SAP invoices
    print("\n📦 Ingesting SAP invoices...")
    sap = SAPIngestor()
    sap.ingest_from_csv('sample_data/sap_invoices.csv')
    sap.close()
    
    # Ingest customer statements
    print("\n📦 Ingesting customer statements...")
    customer = CustomerIngestor()
    customer.ingest_from_csv('sample_data/customer_statements.csv')
    customer.close()
    
    print("\n✅ Ingestion complete!")

if __name__ == "__main__":
    ingest_sample_data()