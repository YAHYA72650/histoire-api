from flask import Blueprint, jsonify, request
from src.models.story import db, Story, Purchase
import json

stories_bp = Blueprint('stories', __name__)

@stories_bp.route('/stories', methods=['GET'])
def get_all_stories():
    """Récupérer toutes les histoires disponibles"""
    try:
        stories = Story.query.all()
        return jsonify({
            'success': True,
            'stories': [story.to_dict() for story in stories]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/stories/<int:story_id>', methods=['GET'])
def get_story(story_id):
    """Récupérer une histoire spécifique"""
    try:
        story = Story.query.get_or_404(story_id)
        return jsonify({
            'success': True,
            'story': story.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/user-purchases/<email>', methods=['GET'])
def get_user_purchases(email):
    """Récupérer les achats d'un utilisateur"""
    try:
        purchases = Purchase.query.filter_by(user_email=email, is_active=True).all()
        
        # Déterminer quelles histoires sont débloquées
        unlocked_stories = set()
        has_unlimited = False
        
        for purchase in purchases:
            if purchase.pack_type == 'unlimited':
                has_unlimited = True
                break
            elif purchase.story_ids:
                story_ids = json.loads(purchase.story_ids)
                unlocked_stories.update(story_ids)
        
        if has_unlimited:
            # Si l'utilisateur a l'accès illimité, débloquer toutes les histoires
            all_stories = Story.query.all()
            unlocked_stories = {story.id for story in all_stories}
        
        return jsonify({
            'success': True,
            'purchases': [purchase.to_dict() for purchase in purchases],
            'unlocked_stories': list(unlocked_stories),
            'has_unlimited': has_unlimited
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/purchase', methods=['POST'])
def create_purchase():
    """Créer un nouvel achat"""
    try:
        data = request.get_json()
        
        required_fields = ['user_email', 'pack_type', 'amount_paid']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }), 400
        
        # Créer l'achat
        purchase = Purchase(
            user_email=data['user_email'],
            pack_type=data['pack_type'],
            story_ids=data.get('story_ids'),
            amount_paid=data['amount_paid'],
            paypal_transaction_id=data.get('paypal_transaction_id')
        )
        
        db.session.add(purchase)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'purchase': purchase.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/packs', methods=['GET'])
def get_packs():
    """Récupérer les informations sur les packs disponibles"""
    packs = [
        {'id': 'single', 'name': '1 Histoire', 'price': 2.99, 'stories': 1},
        {'id': 'pack10', 'name': '10 Histoires', 'price': 24.99, 'stories': 10, 'savings': '17%'},
        {'id': 'pack50', 'name': '50 Histoires', 'price': 99.99, 'stories': 50, 'savings': '33%'},
        {'id': 'pack100', 'name': '100 Histoires', 'price': 179.99, 'stories': 100, 'savings': '40%'},
        {'id': 'unlimited', 'name': 'Collection Complète', 'price': 299.99, 'stories': 'Illimitées', 'savings': '50%'}
    ]
    
    return jsonify({
        'success': True,
        'packs': packs
    })

@stories_bp.route('/init-sample-data', methods=['POST'])
def init_sample_data():
    """Initialiser les données d'exemple"""
    try:
        # Vérifier si des histoires existent déjà
        if Story.query.count() > 0:
            return jsonify({
                'success': True,
                'message': 'Les données d\'exemple existent déjà'
            })
        
        # Créer les histoires d'exemple
        sample_stories = [
            {
                'title': "Le Prophète et l'Araignée",
                'description': "L'histoire miraculeuse de la protection divine",
                'duration': "8:30",
                'category': "Prophètes",
                'price': 2.99,
                'is_premium': True
            },
            {
                'title': "Les Compagnons de la Caverne",
                'description': "Une histoire de foi et de persévérance",
                'duration': "12:15",
                'category': "Coran",
                'price': 2.99,
                'is_premium': True
            },
            {
                'title': "La Générosité d'Abu Bakr",
                'description': "L'exemple de générosité du premier Calife",
                'duration': "6:45",
                'category': "Compagnons",
                'price': 2.99,
                'is_premium': True
            },
            {
                'title': "L'Histoire de Bilal",
                'description': "Le premier muezzin de l'Islam",
                'duration': "10:20",
                'category': "Compagnons",
                'price': 2.99,
                'is_premium': True
            }
        ]
        
        for story_data in sample_stories:
            story = Story(**story_data)
            db.session.add(story)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(sample_stories)} histoires d\'exemple créées'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@stories_bp.route('/user-purchases', methods=['GET'])
def get_user_purchases_by_email():
    """Récupérer les achats d'un utilisateur par email (query param)"""
    try:
        user_email = request.args.get('email')
        if not user_email:
            return jsonify({
                'success': False,
                'error': 'Email utilisateur requis'
            }), 400
        
        purchases = Purchase.query.filter_by(user_email=user_email).all()
        purchases_data = []
        
        for purchase in purchases:
            purchases_data.append({
                'id': purchase.id,
                'pack_type': purchase.pack_type,
                'story_ids': purchase.story_ids,
                'amount_paid': purchase.amount_paid,
                'purchase_date': purchase.purchase_date.isoformat(),
                'paypal_transaction_id': purchase.paypal_transaction_id
            })
        
        return jsonify({
            'success': True,
            'purchases': purchases_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/check-access', methods=['GET'])
def check_story_access():
    """Vérifier si un utilisateur a accès à une histoire"""
    try:
        user_email = request.args.get('email')
        story_id = request.args.get('story_id', type=int)
        
        if not user_email or not story_id:
            return jsonify({
                'success': False,
                'error': 'Email et ID d\'histoire requis'
            }), 400
        
        # Vérifier si l'utilisateur a un accès illimité
        unlimited_purchase = Purchase.query.filter_by(
            user_email=user_email,
            pack_type='unlimited'
        ).first()
        
        if unlimited_purchase:
            return jsonify({
                'success': True,
                'has_access': True
            })
        
        # Vérifier si l'histoire spécifique est dans les achats
        purchases = Purchase.query.filter_by(user_email=user_email).all()
        
        for purchase in purchases:
            if purchase.story_ids:
                story_ids = json.loads(purchase.story_ids)
                if story_id in story_ids:
                    return jsonify({
                        'success': True,
                        'has_access': True
                    })
        
        return jsonify({
            'success': True,
            'has_access': False
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/simulate-purchase', methods=['POST'])
def simulate_purchase():
    """Simuler un achat pour les tests (à supprimer en production)"""
    try:
        data = request.get_json()
        
        required_fields = ['user_email', 'pack_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }), 400
        
        user_email = data['user_email']
        pack_type = data['pack_type']
        story_id = data.get('story_id')
        
        # Déterminer quelles histoires débloquer selon le pack
        story_ids = None
        amount_paid = 0
        
        if pack_type == 'single' and story_id:
            story_ids = json.dumps([story_id])
            amount_paid = 2.99
        elif pack_type == 'pack10':
            stories = Story.query.limit(10).all()
            story_ids = json.dumps([story.id for story in stories])
            amount_paid = 24.99
        elif pack_type == 'pack50':
            stories = Story.query.limit(50).all()
            story_ids = json.dumps([story.id for story in stories])
            amount_paid = 99.99
        elif pack_type == 'pack100':
            stories = Story.query.limit(100).all()
            story_ids = json.dumps([story.id for story in stories])
            amount_paid = 179.99
        elif pack_type == 'unlimited':
            # Pour unlimited, on ne spécifie pas de story_ids
            amount_paid = 249.99
        
        # Créer l'enregistrement d'achat
        purchase = Purchase(
            user_email=user_email,
            pack_type=pack_type,
            story_ids=story_ids,
            amount_paid=amount_paid,
            paypal_transaction_id=f'SIMULATED_TEST_{user_email}'
        )
        
        db.session.add(purchase)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'purchase_id': purchase.id,
            'message': f'Achat simulé: {pack_type}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

