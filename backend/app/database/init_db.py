import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.session import engine, SessionLocal
from app.database.base import Base
from app.models.crm import HCP

def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(HCP).first() is None:
            print("Seeding initial fictional HCP database...")
            hcps = [
                HCP(full_name="Dr. Priya Sharma", specialty="Cardiology", organization="Metro Heart Institute", email="priya.sharma@metroheart.com"),
                HCP(full_name="Dr. Alan Grant", specialty="Oncology", organization="City Cancer Research Center", email="alan.grant@citycancer.org"),
                HCP(full_name="Dr. Sarah Connor", specialty="Endocrinology", organization="Valley Medical Group", email="sarah.connor@valleymed.com"),
                HCP(full_name="Dr. Victor Von Doom", specialty="Neurology", organization="State Health Clinic", email="victor.doom@statehealth.org"),
                HCP(full_name="Dr. Elena Rostova", specialty="Pediatrics", organization="Children's General Hospital", email="elena.rostova@childrensgen.org")
            ]
            db.bulk_save_objects(hcps)
            db.commit()
            print("Seeding completed successfully.")
        else:
            print("Database already seeded.")
    except Exception as e:
        print(f"Error seeding DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
