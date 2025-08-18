from flask import Blueprint, jsonify, request
from src.models.story import db
from src.models.pack import Pack

packs_bp = Blueprint('packs', __name__)

@packs_bp.route('/packs', methods=['GET'])
def get_all_packs():
    """Récupérer tous les packs disponibles"""
    try:
        packs = Pack.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'packs': [pack.to_dict() for pack in packs]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@packs_bp.route('/packs/<pack_id>', methods=['GET'])
def get_pack(pack_id):
    """Récupérer un pack spécifique"""
    try:
        pack = Pack.query.filter_by(pack_id=pack_id, is_active=True).first()
        if not pack:
            return jsonify({
                'success': False,
                'error': 'Pack non trouvé'
            }), 404
        
        return jsonify({
            'success': True,
            'pack': pack.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@packs_bp.route('/packs/<int:pack_db_id>', methods=['PUT'])
def update_pack(pack_db_id):
    """Mettre à jour un pack"""
    try:
        pack = Pack.query.get_or_404(pack_db_id)
        data = request.get_json()
        
        # Mettre à jour les champs modifiables
        if 'name' in data:
            pack.name = data['name']
        if 'price' in data:
            pack.price = float(data['price'])
        if 'original_price' in data:
            pack.original_price = float(data['original_price']) if data['original_price'] else None
        if 'description' in data:
            pack.description = data['description']
        if 'stories_count' in data:
            pack.stories_count = data['stories_count']
        if 'is_active' in data:
            pack.is_active = bool(data['is_active'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'pack': pack.to_dict(),
            'message': 'Pack mis à jour avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@packs_bp.route('/packs', methods=['POST'])
def create_pack():
    """Créer un nouveau pack"""
    try:
        data = request.get_json()
        
        required_fields = ['pack_id', 'name', 'price', 'stories_count']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }), 400
        
        # Vérifier que le pack_id n'existe pas déjà
        existing_pack = Pack.query.filter_by(pack_id=data['pack_id']).first()
        if existing_pack:
            return jsonify({
                'success': False,
                'error': 'Un pack avec cet ID existe déjà'
            }), 400
        
        pack = Pack(
            pack_id=data['pack_id'],
            name=data['name'],
            price=float(data['price']),
            original_price=float(data['original_price']) if data.get('original_price') else None,
            description=data.get('description', ''),
            stories_count=data['stories_count']
        )
        
        db.session.add(pack)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'pack': pack.to_dict(),
            'message': 'Pack créé avec succès'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@packs_bp.route('/packs/<int:pack_db_id>', methods=['DELETE'])
def delete_pack(pack_db_id):
    """Supprimer (désactiver) un pack"""
    try:
        pack = Pack.query.get_or_404(pack_db_id)
        pack.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pack désactivé avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@packs_bp.route('/init-packs', methods=['POST'])
def init_packs():
    """Initialiser les packs par défaut"""
    try:
        success = Pack.init_default_packs()
        if success:
            return jsonify({
                'success': True,
                'message': 'Packs initialisés avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de l\'initialisation des packs'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

