import uvicorn
from app.api.routes import app

if __name__ == "__main__":
    print("=" * 60)
    print("MARICO RECONCILIATION API")
    print("=" * 60)
    print("\n🚀 Starting API server...")
    print("📊 Dashboard: http://localhost:8000/dashboard")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("\n" + "=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )