from flask import Blueprint, jsonify, request
import requests
import json
import os
from src.models.story import db, Purchase, Story

paypal_bp = Blueprint('paypal', __name__)

# Configuration PayPal (à remplacer par vos vraies clés)
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID', 'YOUR_PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET', 'YOUR_PAYPAL_CLIENT_SECRET')
PAYPAL_BASE_URL = os.getenv('PAYPAL_BASE_URL', 'https://api-m.sandbox.paypal.com')  # sandbox pour les tests

def get_paypal_access_token():
    """Obtenir un token d'accès PayPal"""
    url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
    
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'en_US',
    }
    
    data = 'grant_type=client_credentials'
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            data=data, 
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
        )
        
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            return None
    except Exception as e:
        print(f"Erreur lors de l'obtention du token PayPal: {e}")
        return None

@paypal_bp.route('/create-payment', methods=['POST'])
def create_payment():
    """Créer un paiement PayPal"""
    try:
        data = request.get_json()
        
        required_fields = ['pack_id', 'user_email', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }), 400
        
        access_token = get_paypal_access_token()
        if not access_token:
            return jsonify({
                'success': False,
                'error': 'Impossible d\'obtenir le token PayPal'
            }), 500
        
        # Créer la commande PayPal
        url = f"{PAYPAL_BASE_URL}/v2/checkout/orders"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }
        
        # Déterminer la description du pack
        pack_descriptions = {
            'single': '1 Histoire',
            'pack10': '10 Histoires',
            'pack50': '50 Histoires', 
            'pack100': '100 Histoires',
            'unlimited': 'Collection Complète'
        }
        
        pack_description = pack_descriptions.get(data['pack_id'], 'Pack d\'histoires')
        
        payment_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": "EUR",
                    "value": str(data['amount'])
                },
                "description": f"Les histoires de tonton Yahya - {pack_description}"
            }],
            "application_context": {
                "return_url": f"{request.host_url}payment-success",
                "cancel_url": f"{request.host_url}payment-cancel"
            }
        }
        
        response = requests.post(url, headers=headers, json=payment_data)
        
        if response.status_code == 201:
            order = response.json()
            
            # Sauvegarder les informations de commande temporairement
            # (dans une vraie application, vous utiliseriez une base de données)
            
            return jsonify({
                'success': True,
                'order_id': order['id'],
                'approval_url': next(link['href'] for link in order['links'] if link['rel'] == 'approve')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la création du paiement PayPal',
                'details': response.text
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@paypal_bp.route('/capture-payment', methods=['POST'])
def capture_payment():
    """Capturer un paiement PayPal après approbation"""
    try:
        data = request.get_json()
        
        if 'order_id' not in data:
            return jsonify({
                'success': False,
                'error': 'ID de commande manquant'
            }), 400
        
        access_token = get_paypal_access_token()
        if not access_token:
            return jsonify({
                'success': False,
                'error': 'Impossible d\'obtenir le token PayPal'
            }), 500
        
        # Capturer la commande
        url = f"{PAYPAL_BASE_URL}/v2/checkout/orders/{data['order_id']}/capture"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }
        
        response = requests.post(url, headers=headers)
        
        if response.status_code == 201:
            capture_result = response.json()
            
            # Vérifier que le paiement a été capturé avec succès
            if capture_result['status'] == 'COMPLETED':
                # Créer l'enregistrement d'achat dans la base de données
                purchase_data = data.get('purchase_data', {})
                
                # Déterminer quelles histoires débloquer selon le pack
                story_ids = None
                pack_type = purchase_data.get('pack_type', 'single')
                
                if pack_type == 'single':
                    # Pour un achat unique, spécifier l'ID de l'histoire
                    story_ids = json.dumps([purchase_data.get('story_id')])
                elif pack_type in ['pack10', 'pack50', 'pack100']:
                    # Pour les packs, débloquer un nombre spécifique d'histoires
                    pack_sizes = {'pack10': 10, 'pack50': 50, 'pack100': 100}
                    limit = pack_sizes[pack_type]
                    stories = Story.query.limit(limit).all()
                    story_ids = json.dumps([story.id for story in stories])
                # Pour 'unlimited', on ne spécifie pas de story_ids (accès à tout)
                
                purchase = Purchase(
                    user_email=purchase_data.get('user_email'),
                    pack_type=pack_type,
                    story_ids=story_ids,
                    amount_paid=float(capture_result['purchase_units'][0]['payments']['captures'][0]['amount']['value']),
                    paypal_transaction_id=capture_result['id']
                )
                
                db.session.add(purchase)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'transaction_id': capture_result['id'],
                    'purchase_id': purchase.id
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Le paiement n\'a pas été complété'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la capture du paiement',
                'details': response.text
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@paypal_bp.route('/payment-status/<order_id>', methods=['GET'])
def get_payment_status(order_id):
    """Vérifier le statut d'un paiement PayPal"""
    try:
        access_token = get_paypal_access_token()
        if not access_token:
            return jsonify({
                'success': False,
                'error': 'Impossible d\'obtenir le token PayPal'
            }), 500
        
        url = f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            order = response.json()
            return jsonify({
                'success': True,
                'status': order['status'],
                'order': order
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Commande non trouvée'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

