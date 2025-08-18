from src.models.story import db
from datetime import datetime

class Pack(db.Model):
    __tablename__ = 'packs'
    
    id = db.Column(db.Integer, primary_key=True)
    pack_id = db.Column(db.String(50), unique=True, nullable=False)  # 'single', 'pack10', etc.
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float, nullable=True)  # Prix barré pour les économies
    description = db.Column(db.String(200), nullable=True)
    stories_count = db.Column(db.String(20), nullable=False)  # '1', '10', '∞'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'pack_id': self.pack_id,
            'name': self.name,
            'price': self.price,
            'original_price': self.original_price,
            'description': self.description,
            'stories_count': self.stories_count,
            'is_active': self.is_active,
            'savings': self.calculate_savings(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_savings(self):
        """Calculer le pourcentage d'économie"""
        if self.original_price and self.original_price > self.price:
            savings_percent = ((self.original_price - self.price) / self.original_price) * 100
            return f"{int(savings_percent)}%"
        return None
    
    @staticmethod
    def init_default_packs():
        """Initialiser les packs par défaut"""
        default_packs = [
            {
                'pack_id': 'single',
                'name': '1 Histoire',
                'price': 2.99,
                'description': 'Achat unique',
                'stories_count': '1'
            },
            {
                'pack_id': 'pack10',
                'name': '10 Histoires',
                'price': 24.99,
                'original_price': 29.90,
                'description': 'Économisez 16%',
                'stories_count': '10'
            },
            {
                'pack_id': 'pack50',
                'name': '50 Histoires',
                'price': 99.99,
                'original_price': 149.50,
                'description': 'Économisez 33%',
                'stories_count': '50'
            },
            {
                'pack_id': 'pack100',
                'name': '100 Histoires',
                'price': 179.99,
                'original_price': 299.00,
                'description': 'Économisez 40%',
                'stories_count': '100'
            },
            {
                'pack_id': 'unlimited',
                'name': 'Collection Complète',
                'price': 249.99,
                'description': 'Accès illimité + futures histoires',
                'stories_count': '∞'
            }
        ]
        
        for pack_data in default_packs:
            existing_pack = Pack.query.filter_by(pack_id=pack_data['pack_id']).first()
            if not existing_pack:
                pack = Pack(**pack_data)
                db.session.add(pack)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de l'initialisation des packs: {e}")
            return False

