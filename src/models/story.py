from src.models.user import db
from datetime import datetime

class Story(db.Model):
    __tablename__ = 'stories'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    duration = db.Column(db.String(10), nullable=False)  # Format: "8:30"
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    audio_file_path = db.Column(db.String(500), nullable=True)
    is_premium = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'duration': self.duration,
            'category': self.category,
            'price': self.price,
            'audio_file_path': self.audio_file_path,
            'is_premium': self.is_premium,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Purchase(db.Model):
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(200), nullable=False)
    pack_type = db.Column(db.String(50), nullable=False)  # 'single', 'pack10', 'pack50', 'pack100', 'unlimited'
    story_ids = db.Column(db.Text, nullable=True)  # JSON string of story IDs for specific purchases
    amount_paid = db.Column(db.Float, nullable=False)
    paypal_transaction_id = db.Column(db.String(200), nullable=True)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_email': self.user_email,
            'pack_type': self.pack_type,
            'story_ids': self.story_ids,
            'amount_paid': self.amount_paid,
            'paypal_transaction_id': self.paypal_transaction_id,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'is_active': self.is_active
        }

