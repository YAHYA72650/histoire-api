from flask import Blueprint, jsonify, request, render_template_string, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os
from src.models.story import db, Story, Purchase
import json

admin_bp = Blueprint('admin', __name__)

# Configuration pour l'upload de fichiers
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'audio')
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}

# Créer le dossier audio s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Mot de passe admin simple (à remplacer par un système plus sécurisé)
ADMIN_PASSWORD_HASH = generate_password_hash('admin123')  # Changez ce mot de passe !

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    """Décorateur pour vérifier l'authentification admin"""
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    """Page de connexion admin"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Mot de passe incorrect', 'error')
    
    login_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Administration - Les histoires de tonton Yahya</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            input[type="password"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a87; }
            .error { color: red; margin-top: 10px; }
        </style>
    </head>
    <body>
        <h2>Administration</h2>
        <form method="post">
            <div class="form-group">
                <label for="password">Mot de passe :</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">Se connecter</button>
        </form>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="error">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </body>
    </html>
    '''
    return render_template_string(login_template)

@admin_bp.route('/admin/logout')
def logout():
    """Déconnexion admin"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))

@admin_bp.route('/admin')
@login_required
def dashboard():
    """Tableau de bord admin"""
    stories = Story.query.all()
    purchases = Purchase.query.order_by(Purchase.purchase_date.desc()).limit(10).all()
    
    dashboard_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Administration - Les histoires de tonton Yahya</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            .header { background: #007cba; color: white; padding: 15px; margin: -20px -20px 20px -20px; }
            .nav { margin-bottom: 20px; }
            .nav a { margin-right: 15px; color: #007cba; text-decoration: none; }
            .nav a:hover { text-decoration: underline; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
            th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
            th { background: #f5f5f5; }
            .btn { background: #007cba; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; }
            .btn:hover { background: #005a87; }
            .btn-danger { background: #dc3545; }
            .btn-danger:hover { background: #c82333; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Administration - Les histoires de tonton Yahya</h1>
        </div>
        
        <div class="nav">
            <a href="{{ url_for('admin.dashboard') }}">Tableau de bord</a>
            <a href="{{ url_for('admin.add_story') }}">Ajouter une histoire</a>
            <a href="{{ url_for('admin.manage_packs') }}">Gérer les packs</a>
            <a href="{{ url_for('admin.logout') }}">Déconnexion</a>
        </div>
        
        <h2>Histoires ({{ stories|length }})</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Titre</th>
                <th>Catégorie</th>
                <th>Durée</th>
                <th>Prix</th>
                <th>Fichier audio</th>
                <th>Actions</th>
            </tr>
            {% for story in stories %}
            <tr>
                <td>{{ story.id }}</td>
                <td>{{ story.title }}</td>
                <td>{{ story.category }}</td>
                <td>{{ story.duration }}</td>
                <td>{{ story.price }}€</td>
                <td>{{ 'Oui' if story.audio_file_path else 'Non' }}</td>
                <td>
                    <a href="{{ url_for('admin.edit_story', story_id=story.id) }}" class="btn">Modifier</a>
                    <a href="{{ url_for('admin.delete_story', story_id=story.id) }}" class="btn btn-danger" onclick="return confirm('Êtes-vous sûr ?')">Supprimer</a>
                </td>
            </tr>
            {% endfor %}
        </table>
        
        <h2>Derniers achats</h2>
        <table>
            <tr>
                <th>Date</th>
                <th>Email</th>
                <th>Pack</th>
                <th>Montant</th>
                <th>Transaction PayPal</th>
            </tr>
            {% for purchase in purchases %}
            <tr>
                <td>{{ purchase.purchase_date.strftime('%d/%m/%Y %H:%M') }}</td>
                <td>{{ purchase.user_email }}</td>
                <td>{{ purchase.pack_type }}</td>
                <td>{{ purchase.amount_paid }}€</td>
                <td>{{ purchase.paypal_transaction_id[:20] }}...</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''
    return render_template_string(dashboard_template, stories=stories, purchases=purchases)

@admin_bp.route('/admin/add-story', methods=['GET', 'POST'])
@login_required
def add_story():
    """Ajouter une nouvelle histoire"""
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            title = request.form.get('title')
            description = request.form.get('description')
            duration = request.form.get('duration')
            category = request.form.get('category')
            price = float(request.form.get('price', 0))
            
            # Gérer l'upload du fichier audio
            audio_file_path = None
            if 'audio_file' in request.files:
                file = request.files['audio_file']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    audio_file_path = f'/static/audio/{filename}'
            
            # Créer la nouvelle histoire
            story = Story(
                title=title,
                description=description,
                duration=duration,
                category=category,
                price=price,
                audio_file_path=audio_file_path,
                is_premium=True
            )
            
            db.session.add(story)
            db.session.commit()
            
            flash('Histoire ajoutée avec succès !', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'ajout : {str(e)}', 'error')
    
    add_story_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ajouter une histoire - Administration</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            .header { background: #007cba; color: white; padding: 15px; margin: -20px -20px 20px -20px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            textarea { height: 100px; resize: vertical; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a87; }
            .back-link { color: #007cba; text-decoration: none; }
            .back-link:hover { text-decoration: underline; }
            .success { color: green; margin-bottom: 15px; }
            .error { color: red; margin-bottom: 15px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Ajouter une nouvelle histoire</h1>
        </div>
        
        <a href="{{ url_for('admin.dashboard') }}" class="back-link">← Retour au tableau de bord</a>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="post" enctype="multipart/form-data">
            <div class="form-group">
                <label for="title">Titre :</label>
                <input type="text" id="title" name="title" required>
            </div>
            
            <div class="form-group">
                <label for="description">Description :</label>
                <textarea id="description" name="description" required></textarea>
            </div>
            
            <div class="form-group">
                <label for="duration">Durée (ex: 8:30) :</label>
                <input type="text" id="duration" name="duration" placeholder="8:30" required>
            </div>
            
            <div class="form-group">
                <label for="category">Catégorie :</label>
                <select id="category" name="category" required>
                    <option value="">Choisir une catégorie</option>
                    <option value="Prophètes">Prophètes</option>
                    <option value="Compagnons">Compagnons</option>
                    <option value="Coran">Coran</option>
                    <option value="Morale">Morale</option>
                    <option value="Histoire">Histoire</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="price">Prix (€) :</label>
                <input type="number" id="price" name="price" step="0.01" value="2.99" required>
            </div>
            
            <div class="form-group">
                <label for="audio_file">Fichier audio (MP3, WAV, OGG, M4A) :</label>
                <input type="file" id="audio_file" name="audio_file" accept=".mp3,.wav,.ogg,.m4a">
            </div>
            
            <button type="submit">Ajouter l'histoire</button>
        </form>
    </body>
    </html>
    '''
    return render_template_string(add_story_template)

@admin_bp.route('/admin/edit-story/<int:story_id>', methods=['GET', 'POST'])
@login_required
def edit_story(story_id):
    """Modifier une histoire existante"""
    story = Story.query.get_or_404(story_id)
    
    if request.method == 'POST':
        try:
            # Mettre à jour les données
            story.title = request.form.get('title')
            story.description = request.form.get('description')
            story.duration = request.form.get('duration')
            story.category = request.form.get('category')
            story.price = float(request.form.get('price', 0))
            
            # Gérer l'upload d'un nouveau fichier audio
            if 'audio_file' in request.files:
                file = request.files['audio_file']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    story.audio_file_path = f'/static/audio/{filename}'
            
            db.session.commit()
            flash('Histoire modifiée avec succès !', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification : {str(e)}', 'error')
    
    # Template similaire à add_story mais avec les valeurs pré-remplies
    edit_story_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Modifier une histoire - Administration</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            .header { background: #007cba; color: white; padding: 15px; margin: -20px -20px 20px -20px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            textarea { height: 100px; resize: vertical; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a87; }
            .back-link { color: #007cba; text-decoration: none; }
            .back-link:hover { text-decoration: underline; }
            .success { color: green; margin-bottom: 15px; }
            .error { color: red; margin-bottom: 15px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Modifier l'histoire : {{ story.title }}</h1>
        </div>
        
        <a href="{{ url_for('admin.dashboard') }}" class="back-link">← Retour au tableau de bord</a>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="post" enctype="multipart/form-data">
            <div class="form-group">
                <label for="title">Titre :</label>
                <input type="text" id="title" name="title" value="{{ story.title }}" required>
            </div>
            
            <div class="form-group">
                <label for="description">Description :</label>
                <textarea id="description" name="description" required>{{ story.description }}</textarea>
            </div>
            
            <div class="form-group">
                <label for="duration">Durée (ex: 8:30) :</label>
                <input type="text" id="duration" name="duration" value="{{ story.duration }}" required>
            </div>
            
            <div class="form-group">
                <label for="category">Catégorie :</label>
                <select id="category" name="category" required>
                    <option value="Prophètes" {{ 'selected' if story.category == 'Prophètes' else '' }}>Prophètes</option>
                    <option value="Compagnons" {{ 'selected' if story.category == 'Compagnons' else '' }}>Compagnons</option>
                    <option value="Coran" {{ 'selected' if story.category == 'Coran' else '' }}>Coran</option>
                    <option value="Morale" {{ 'selected' if story.category == 'Morale' else '' }}>Morale</option>
                    <option value="Histoire" {{ 'selected' if story.category == 'Histoire' else '' }}>Histoire</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="price">Prix (€) :</label>
                <input type="number" id="price" name="price" step="0.01" value="{{ story.price }}" required>
            </div>
            
            <div class="form-group">
                <label for="audio_file">Nouveau fichier audio (optionnel) :</label>
                <input type="file" id="audio_file" name="audio_file" accept=".mp3,.wav,.ogg,.m4a">
                {% if story.audio_file_path %}
                    <p>Fichier actuel : {{ story.audio_file_path }}</p>
                {% endif %}
            </div>
            
            <button type="submit">Modifier l'histoire</button>
        </form>
    </body>
    </html>
    '''
    return render_template_string(edit_story_template, story=story)

@admin_bp.route('/admin/delete-story/<int:story_id>')
@login_required
def delete_story(story_id):
    """Supprimer une histoire"""
    try:
        story = Story.query.get_or_404(story_id)
        
        # Supprimer le fichier audio s'il existe
        if story.audio_file_path:
            file_path = os.path.join(os.path.dirname(__file__), '..', 'static', story.audio_file_path.lstrip('/static/'))
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.session.delete(story)
        db.session.commit()
        
        flash('Histoire supprimée avec succès !', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'error')
    
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/admin/packs')
@login_required
def manage_packs():
    """Page de gestion des packs"""
    from src.models.pack import Pack
    
    packs = Pack.query.filter_by(is_active=True).all()
    
    packs_template = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gestion des Packs - Administration</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #3b82f6; color: white; padding: 20px; margin: -20px -20px 20px -20px; }}
            .nav {{ margin: 20px 0; }}
            .nav a {{ display: inline-block; padding: 10px 15px; margin-right: 10px; background: #10b981; color: white; text-decoration: none; border-radius: 5px; }}
            .nav a:hover {{ background: #059669; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .btn {{ padding: 8px 12px; margin: 2px; text-decoration: none; border-radius: 4px; font-size: 12px; }}
            .btn-edit {{ background: #3b82f6; color: white; }}
            .btn-delete {{ background: #ef4444; color: white; }}
            .btn-add {{ background: #10b981; color: white; padding: 10px 20px; font-size: 14px; }}
            .form-group {{ margin: 15px 0; }}
            .form-group label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            .form-group input, .form-group textarea {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
            .savings {{ color: #10b981; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Gestion des Packs d'Achat</h1>
        </div>
        
        <div class="nav">
            <a href="/admin">Tableau de bord</a>
            <a href="/admin/add-story">Ajouter une histoire</a>
            <a href="/admin/packs">Gérer les packs</a>
            <a href="/admin/logout">Déconnexion</a>
        </div>
        
        <div style="margin: 20px 0;">
            <a href="/admin/add-pack" class="btn btn-add">Ajouter un nouveau pack</a>
        </div>
        
        <h2>Packs d'achat ({len(packs)})</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nom</th>
                    <th>Prix</th>
                    <th>Prix original</th>
                    <th>Économies</th>
                    <th>Histoires</th>
                    <th>Description</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for pack in packs:
        savings = pack.calculate_savings() or ''
        original_price = f"{pack.original_price}€" if pack.original_price else '-'
        
        packs_template += f'''
                <tr>
                    <td>{pack.pack_id}</td>
                    <td>{pack.name}</td>
                    <td><strong>{pack.price}€</strong></td>
                    <td>{original_price}</td>
                    <td class="savings">{savings}</td>
                    <td>{pack.stories_count}</td>
                    <td>{pack.description}</td>
                    <td>
                        <a href="/admin/edit-pack/{pack.id}" class="btn btn-edit">Modifier</a>
                        <a href="/admin/delete-pack/{pack.id}" class="btn btn-delete" 
                           onclick="return confirm('Êtes-vous sûr de vouloir supprimer ce pack ?')">Supprimer</a>
                    </td>
                </tr>
        '''
    
    packs_template += '''
            </tbody>
        </table>
        
        <script>
            // Auto-refresh toutes les 30 secondes pour voir les changements
            setTimeout(() => location.reload(), 30000);
        </script>
    </body>
    </html>
    '''
    
    return packs_template

@admin_bp.route('/admin/add-pack', methods=['GET', 'POST'])
@login_required
def add_pack():
    """Ajouter un nouveau pack"""
    from src.models.pack import Pack
    
    if request.method == 'POST':
        try:
            pack = Pack(
                pack_id=request.form['pack_id'],
                name=request.form['name'],
                price=float(request.form['price']),
                original_price=float(request.form['original_price']) if request.form['original_price'] else None,
                description=request.form['description'],
                stories_count=request.form['stories_count']
            )
            
            db.session.add(pack)
            db.session.commit()
            flash('Pack ajouté avec succès !', 'success')
            return redirect(url_for('admin.manage_packs'))
        except Exception as e:
            flash(f'Erreur lors de l\'ajout du pack: {str(e)}', 'error')
    
    add_pack_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ajouter un Pack - Administration</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background: #3b82f6; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
            .nav { margin: 20px 0; }
            .nav a { display: inline-block; padding: 10px 15px; margin-right: 10px; background: #10b981; color: white; text-decoration: none; border-radius: 5px; }
            .form-group { margin: 15px 0; }
            .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
            .form-group input, .form-group textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            .btn { padding: 10px 20px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .btn:hover { background: #2563eb; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Ajouter un nouveau pack</h1>
        </div>
        
        <div class="nav">
            <a href="/admin/packs">← Retour aux packs</a>
        </div>
        
        <form method="POST">
            <div class="form-group">
                <label>ID du pack (ex: pack25) :</label>
                <input type="text" name="pack_id" required>
            </div>
            
            <div class="form-group">
                <label>Nom :</label>
                <input type="text" name="name" required>
            </div>
            
            <div class="form-group">
                <label>Prix (€) :</label>
                <input type="number" step="0.01" name="price" required>
            </div>
            
            <div class="form-group">
                <label>Prix original (€) - optionnel :</label>
                <input type="number" step="0.01" name="original_price">
            </div>
            
            <div class="form-group">
                <label>Nombre d'histoires :</label>
                <input type="text" name="stories_count" required placeholder="ex: 25 ou ∞">
            </div>
            
            <div class="form-group">
                <label>Description :</label>
                <textarea name="description" rows="3"></textarea>
            </div>
            
            <button type="submit" class="btn">Ajouter le pack</button>
        </form>
    </body>
    </html>
    '''
    
    return add_pack_template

@admin_bp.route('/admin/edit-pack/<int:pack_id>', methods=['GET', 'POST'])
@login_required
def edit_pack(pack_id):
    """Modifier un pack existant"""
    from src.models.pack import Pack
    
    pack = Pack.query.get_or_404(pack_id)
    
    if request.method == 'POST':
        try:
            pack.name = request.form['name']
            pack.price = float(request.form['price'])
            pack.original_price = float(request.form['original_price']) if request.form['original_price'] else None
            pack.description = request.form['description']
            pack.stories_count = request.form['stories_count']
            
            db.session.commit()
            flash('Pack modifié avec succès !', 'success')
            return redirect(url_for('admin.manage_packs'))
        except Exception as e:
            flash(f'Erreur lors de la modification: {str(e)}', 'error')
    
    edit_pack_template = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Modifier le pack : {pack.name}</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #3b82f6; color: white; padding: 20px; margin: -20px -20px 20px -20px; }}
            .nav {{ margin: 20px 0; }}
            .nav a {{ display: inline-block; padding: 10px 15px; margin-right: 10px; background: #10b981; color: white; text-decoration: none; border-radius: 5px; }}
            .form-group {{ margin: 15px 0; }}
            .form-group label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            .form-group input, .form-group textarea {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
            .btn {{ padding: 10px 20px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer; }}
            .btn:hover {{ background: #2563eb; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Modifier le pack : {pack.name}</h1>
        </div>
        
        <div class="nav">
            <a href="/admin/packs">← Retour aux packs</a>
        </div>
        
        <form method="POST">
            <div class="form-group">
                <label>Nom :</label>
                <input type="text" name="name" value="{pack.name}" required>
            </div>
            
            <div class="form-group">
                <label>Prix (€) :</label>
                <input type="number" step="0.01" name="price" value="{pack.price}" required>
            </div>
            
            <div class="form-group">
                <label>Prix original (€) - optionnel :</label>
                <input type="number" step="0.01" name="original_price" value="{pack.original_price or ''}">
            </div>
            
            <div class="form-group">
                <label>Nombre d'histoires :</label>
                <input type="text" name="stories_count" value="{pack.stories_count}" required>
            </div>
            
            <div class="form-group">
                <label>Description :</label>
                <textarea name="description" rows="3">{pack.description}</textarea>
            </div>
            
            <button type="submit" class="btn">Modifier le pack</button>
        </form>
    </body>
    </html>
    '''
    
    return edit_pack_template

@admin_bp.route('/admin/delete-pack/<int:pack_id>')
@login_required
def delete_pack(pack_id):
    """Supprimer (désactiver) un pack"""
    from src.models.pack import Pack
    
    try:
        pack = Pack.query.get_or_404(pack_id)
        pack.is_active = False
        db.session.commit()
        flash('Pack supprimé avec succès !', 'success')
    except Exception as e:
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_packs'))

