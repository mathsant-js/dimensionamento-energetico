from sqlalchemy.orm import Session
from app import models, schemas

# Sample equipment data - based on common household appliances
SAMPLE_EQUIPMENTS = [
    {"name": "Geladeira", "category": "Refrigeração", "power_watts": 500},
    {"name": "Freezer", "category": "Refrigeração", "power_watts": 600},
    {"name": "Ar Condicionado 12000 BTU", "category": "Climatização", "power_watts": 1500},
    {"name": "Ar Condicionado 18000 BTU", "category": "Climatização", "power_watts": 2000},
    {"name": "Ventilador", "category": "Climatização", "power_watts": 60},
    {"name": "Chuveiro Elétrico", "category": "Aquecimento", "power_watts": 5500},
    {"name": "Aquecedor de Água", "category": "Aquecimento", "power_watts": 3000},
    {"name": "Ferro de Passar", "category": "Limpeza", "power_watts": 1000},
    {"name": "Máquina de Lavar", "category": "Limpeza", "power_watts": 2000},
    {"name": "Micro-ondas", "category": "Cozinha", "power_watts": 1200},
    {"name": "Forno Elétrico", "category": "Cozinha", "power_watts": 3500},
    {"name": "Fogão Elétrico", "category": "Cozinha", "power_watts": 8000},
    {"name": "Liquidificador", "category": "Cozinha", "power_watts": 500},
    {"name": "Televisão", "category": "Entretenimento", "power_watts": 150},
    {"name": "Computador Desktop", "category": "Eletrônicos", "power_watts": 300},
    {"name": "Notebook", "category": "Eletrônicos", "power_watts": 100},
    {"name": "Impressora", "category": "Eletrônicos", "power_watts": 200},
    {"name": "Luz LED", "category": "Iluminação", "power_watts": 15},
    {"name": "Luz Fluorescente", "category": "Iluminação", "power_watts": 40},
    {"name": "Secadora de Roupa", "category": "Limpeza", "power_watts": 3500},
]

def seed_equipments(db: Session):
    """Seed the database with sample equipment data"""
    # Check if equipments already exist
    existing_count = db.query(models.Equipment).count()
    if existing_count > 0:
        return
    
    for equipment_data in SAMPLE_EQUIPMENTS:
        equipment = models.Equipment(
            name=equipment_data["name"],
            category=equipment_data["category"],
            power_watts=equipment_data["power_watts"],
        )
        db.add(equipment)
    
    db.commit()
