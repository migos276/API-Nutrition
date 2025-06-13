from flask import Flask, request, jsonify
import sqlite3
import time
import json
import os
import requests
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict
import uuid
from PIL import Image
import io
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
import mimetypes

app = Flask(__name__)

# Configuration de base
MEDIA_FOLDER = 'media'
if not os.path.exists(MEDIA_FOLDER):
    os.makedirs(MEDIA_FOLDER)

# DAO Pattern - Data Access Objects
class DatabaseDAO:
    def __init__(self, db_name='allergy_detection.db'):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table des utilisateurs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des aliments
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS foods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    ingredients TEXT,
                    image_path TEXT,
                    is_base_food BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Table des repas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS meals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    food_id INTEGER,
                    meal_time TIMESTAMP,
                    quantity REAL,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (food_id) REFERENCES foods (id)
                )
            ''')
            
            # Table des symptômes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS symptoms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    symptom_type TEXT NOT NULL,
                    severity INTEGER CHECK(severity >= 1 AND severity <= 5),
                    occurrence_time TIMESTAMP,
                    description TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Table de planification hebdomadaire
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weekly_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    week_start_date DATE,
                    day_of_week INTEGER CHECK(day_of_week >= 0 AND day_of_week <= 6),
                    meal_type TEXT NOT NULL,
                    food_id INTEGER,
                    planned_quantity REAL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (food_id) REFERENCES foods (id)
                )
            ''')
            
            # Table de gestion de buffet
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS buffet_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name TEXT NOT NULL,
                    event_date DATE,
                    estimated_guests INTEGER,
                    created_by INTEGER,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS buffet_foods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    buffet_id INTEGER,
                    food_id INTEGER,
                    planned_quantity REAL,
                    unit TEXT DEFAULT 'portions',
                    FOREIGN KEY (buffet_id) REFERENCES buffet_events (id),
                    FOREIGN KEY (food_id) REFERENCES foods (id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS food_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    food_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    original_url TEXT,
                    is_primary BOOLEAN DEFAULT 0,
                    file_size INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (food_id) REFERENCES foods (id) ON DELETE CASCADE
);
        ''')
            
            conn.commit()

class UserDAO:
    def __init__(self, db_dao):
        self.db = db_dao
    
    def create_user(self, username, email):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (username, email) VALUES (?, ?)",
                    (username, email)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None
    def get_user(self, user_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            return cursor.fetchone()
    
    def get_all_users(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            return cursor.fetchall()
    def update_user(self, user_id, username=None, email=None):
        """Mettre à jour les informations d'un utilisateur"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Construire la requête dynamiquement
            updates = []
            params = []
            
            if username is not None:
                updates.append("username = ?")
                params.append(username)
            
            if email is not None:
                updates.append("email = ?")
                params.append(email)
            
            if not updates:
                return False
            
            params.append(user_id)
            
            try:
                cursor.execute(
                    f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                    params
                )
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False

    def delete_user(self, user_id):
        """Supprimer un utilisateur et toutes ses données associées"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Supprimer d'abord toutes les données associées
                cursor.execute("DELETE FROM symptoms WHERE user_id = ?", (user_id,))
                cursor.execute("DELETE FROM meals WHERE user_id = ?", (user_id,))
                cursor.execute("DELETE FROM weekly_plans WHERE user_id = ?", (user_id,))
                cursor.execute("DELETE FROM buffet_events WHERE created_by = ?", (user_id,))
                
                # Supprimer l'utilisateur
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                
                conn.commit()
                return cursor.rowcount > 0
            except Exception:
                conn.rollback()
                return False

    def user_exists(self, user_id):
        """Vérifier si un utilisateur existe"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
            return cursor.fetchone() is not None

class FoodDAO:
    def __init__(self, db_dao):
        self.db = db_dao
    
    def create_food(self, name, category, ingredients, image_path=None, is_base_food=False):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO foods (name, category, ingredients, image_path, is_base_food) VALUES (?, ?, ?, ?, ?)",
                (name, category, ingredients, image_path, is_base_food)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_food(self, food_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM foods WHERE id = ?", (food_id,))
            return cursor.fetchone()
    
    def get_all_foods(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM foods")
            return cursor.fetchall()
    
    def search_foods(self, query):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM foods WHERE name LIKE ? OR category LIKE ? OR ingredients LIKE ?",
                (f"%{query}%", f"%{query}%", f"%{query}%")
            )
            return cursor.fetchall()

class MealDAO:
    def __init__(self, db_dao):
        self.db = db_dao
    
    def create_meal(self, user_id, food_id, meal_time, quantity, notes=None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO meals (user_id, food_id, meal_time, quantity, notes) VALUES (?, ?, ?, ?, ?)",
                (user_id, food_id, meal_time, quantity, notes)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_user_meals(self, user_id, start_date=None, end_date=None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT m.*, f.name as food_name, f.ingredients 
                FROM meals m 
                JOIN foods f ON m.food_id = f.id 
                WHERE m.user_id = ?
            """
            params = [user_id]
            
            if start_date:
                query += " AND m.meal_time >= ?"
                params.append(start_date)
            if end_date:
                query += " AND m.meal_time <= ?"
                params.append(end_date)
            
            query += " ORDER BY m.meal_time DESC"
            cursor.execute(query, params)
            return cursor.fetchall()

class SymptomDAO:
    def __init__(self, db_dao):
        self.db = db_dao
    
    def create_symptom(self, user_id, symptom_type, severity, occurrence_time, description=None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO symptoms (user_id, symptom_type, severity, occurrence_time, description) VALUES (?, ?, ?, ?, ?)",
                (user_id, symptom_type, severity, occurrence_time, description)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_user_symptoms(self, user_id, start_date=None, end_date=None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM symptoms WHERE user_id = ?"
            params = [user_id]
            
            if start_date:
                query += " AND occurrence_time >= ?"
                params.append(start_date)
            if end_date:
                query += " AND occurrence_time <= ?"
                params.append(end_date)
            
            query += " ORDER BY occurrence_time DESC"
            cursor.execute(query, params)
            return cursor.fetchall()
class ImageManager:
    def __init__(self, media_folder='media'):
        self.media_folder = media_folder
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        
    def download_and_save_image(self, image_url, food_id, food_name, is_primary=False):
        """Télécharger une image depuis une URL et la sauvegarder localement"""
        try:
            # Créer le dossier media s'il n'existe pas
            if not os.path.exists(self.media_folder):
                os.makedirs(self.media_folder)
            
            # Télécharger l'image
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Déterminer l'extension du fichier
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type:
                return {'success': False, 'error': 'URL ne pointe pas vers une image'}
            
            # Récupérer l'extension depuis l'URL ou le content-type
            parsed_url = urlparse(image_url)
            file_extension = os.path.splitext(parsed_url.path)[1].lower()
            
            if not file_extension:
                # Essayer de deviner depuis le content-type
                extension_map = {
                    'image/jpeg': '.jpg',
                    'image/png': '.png',
                    'image/gif': '.gif',
                    'image/webp': '.webp'
                }
                file_extension = extension_map.get(content_type, '.jpg')
            
            # Créer un nom de fichier sécurisé
            safe_name = secure_filename(food_name.replace(' ', '_'))
            timestamp = str(int(time.time()))
            filename = f"{safe_name}_{timestamp}{file_extension}"
            file_path = os.path.join(self.media_folder, filename)
            
            # Sauvegarder l'image
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': filename,
                'file_size': len(response.content),
                'content_type': content_type
            }
            
        except requests.RequestException as e:
            return {'success': False, 'error': f'Erreur de téléchargement: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Erreur: {str(e)}'}
# Initialisation des DAOs
db_dao = DatabaseDAO()
user_dao = UserDAO(db_dao)
food_dao = FoodDAO(db_dao)
meal_dao = MealDAO(db_dao)
symptom_dao = SymptomDAO(db_dao)

# Données de base des nourritures camerounaises
CAMEROON_FOODS_DATA = [
    {
        "name": "Ndolé",
        "category": "Plat principal",
        "ingredients": "feuilles de ndolé, arachides, poisson, viande, crevettes, huile de palme",
        "image_urls": [
            "https://upload.wikimedia.org/wikipedia/commons/2/2f/Le_ndol%C3%A8%2C_plat_mythique_camerounais..jpg",
            "https://upload.wikimedia.org/wikipedia/commons/3/3d/Le_ndol%C3%A8%2C_plat_mythique_camerounais..jpg",
            "https://i.pinimg.com/736x/22/47/d3/2247d3b49942e2dfb832e368c60defc1.jpg",
            "https://i.pinimg.com/736x/81/e4/08/81e4084d05748eaf46acc873e62844eb.jpg",
            "https://i.pinimg.com/736x/bb/10/e5/bb10e5ce9daebc98905c33f043e3cd35.jpg",
            "https://i.pinimg.com/736x/13/3b/8a/133b8a7980d201e39ced44f4e86e0e20.jpg",
            "https://i.pinimg.com/736x/17/16/ab/1716ab632963d4fa5ee00b6c69be210c.jpg",
            "https://i.pinimg.com/736x/e6/5d/ab/e65dab7c6c3199af694c4480ac583fd2.jpg",
            "https://i.pinimg.com/736x/68/6e/f6/686ef640493ab11c4427a2588fec055f.jpg",
            "https://i.pinimg.com/736x/8c/b0/77/8cb077e8f26299555a5ace4e9f796fc6.jpg",
            "https://i.pinimg.com/736x/e4/36/d9/e436d93a6bc2a772f621c86d905ef419.jpg",
            "https://i.pinimg.com/736x/24/1c/c8/241cc8a53f32bcf10448827157ca9b0a.jpg"
        ]
    },
    {
        "name": "Poulet DG",
        "category": "Plat principal", 
        "ingredients": "poulet, plantain, carotte, haricots verts, ail, gingembre",
        "image_urls": [
            "https://i.pinimg.com/736x/e4/25/e7/e425e748dd10a06a4cfc56a60efddf01.jpg",
            "https://i.pinimg.com/736x/46/78/2a/46782a5ccea52063ad03aa464b2fbb64.jpg",
            "https://i.pinimg.com/736x/18/f7/f4/18f7f4b72993a75580aca192e400fc3e.jpg",
            "https://i.pinimg.com/736x/6b/fc/cf/6bfccf9ce9609f1e045b4973b5d55e3a.jpg",
            "https://i.pinimg.com/736x/1c/c4/33/1cc43351b81b40b4c9fb1579235cccbc.jpg",
            "https://i.pinimg.com/736x/ba/7a/e2/ba7ae2e6fc0f44c6c5d08ed2f2edc268.jpg",
            "https://i.pinimg.com/736x/8b/e2/49/8be249e2b95011e212a5f50a79ef121e.jpg",
            "https://i.pinimg.com/736x/bd/93/0b/bd930b9e3fd036a1bc3cca5caa5f5294.jpg",
            "https://i.pinimg.com/736x/a2/a5/2f/a2a52fdea1bcc5156c2fb1446ed6d188.jpg",
            "https://i.pinimg.com/736x/aa/e7/ff/aae7ff9e3ae262ab6117a5ecc50a2398.jpg"
        ]
    },
    {
        "name": "Koki",
        "category": "Plat principal",
        "ingredients": "haricots blancs, huile de palme, feuilles de bananier, épices",
        "image_urls": [
            "https://i.pinimg.com/736x/77/a6/c1/77a6c10851beaae57e33649128d18858.jpg",
            "https://i.pinimg.com/736x/a6/e7/50/a6e750d5cea7e3f0c393c7efe46e99d2.jpg",
            "https://i.pinimg.com/736x/b5/be/5d/b5be5d549d0c25e506a6185618809fcc.jpg",
            "https://i.pinimg.com/736x/1b/73/61/1b7361e9b1610fd0ea74d0ba6a661e0f.jpg",
            "https://i.pinimg.com/736x/84/ff/d5/84ffd5a4edbb16f97c2aa890d0fb9209.jpg",
            "https://i.pinimg.com/736x/af/5d/1b/af5d1b1acf41f30d514d2b8aa96d0669.jpg",
            "https://i.pinimg.com/736x/4d/42/ea/4d42ea58452b14b78a5b1faf3de981ae.jpg",
            "https://i.pinimg.com/736x/52/82/70/528270a792c36ac26277f16f13dda7e3.jpg",
            "https://i.pinimg.com/736x/02/2c/40/022c408b2bff0b0caee701b23d8bfff9.jpg",
            "https://i.pinimg.com/736x/d6/c9/94/d6c9942b7dcc29d19f6263f2c9dbcbfc.jpg",
            "https://i.pinimg.com/736x/93/28/c6/9328c6e13da635b582b28fb59595b04a.jpg",
            "https://i.pinimg.com/736x/2b/6a/dd/2b6add4e18f0e5d8e723068228076555.jpg",
            "https://i.pinimg.com/736x/82/73/d9/8273d96515c5630042cf69a0738f9c80.jpg"
        ]
    },
    {
        "name": "Eru",
        "category": "Plat principal",
        "ingredients": "feuilles d'eru, poisson fumé, viande, huile de palme, épices",
        "image_urls": [
            "https://i.pinimg.com/736x/c0/4d/73/c04d737c2058f08e68eaf0ce861d1abc.jpg",
            "https://i.pinimg.com/736x/9e/ff/38/9eff38cb890d22b55a74de2ff440bb60.jpg",
            "https://i.pinimg.com/736x/f1/47/07/f147078951a725f79b34dc9be59c6ce9.jpg",
            "https://i.pinimg.com/736x/01/b9/1d/01b91d62c520ddeacfb42b58df26dfa2.jpg",
            "https://i.pinimg.com/736x/11/2d/34/112d34bde0425cf778b20e138d5d1ad3.jpg",
            "https://i.pinimg.com/736x/eb/e6/90/ebe690f9aa234a521ce7279f6a7231b5.jpg",
            "https://i.pinimg.com/736x/78/89/a4/7889a488dba0468edfe3d3051e70f1d3.jpg",
            "https://i.pinimg.com/736x/dd/43/db/dd43dbac56ef41a732961aa61888effd.jpg",
            "https://i.pinimg.com/736x/34/1e/79/341e79242a2c08317981e0fffada0524.jpg",
            "https://i.pinimg.com/736x/0d/89/33/0d893361fcb51c3b756abb7ba0049433.jpg",
            ""
        ]
    },
    {
        "name": "Mbongo Tchobi",
        "category": "Plat principal",
        "ingredients": "poisson, épices mbongo, tomates, oignons, ail",
        "image_urls": [
            "https://i.pinimg.com/736x/50/59/42/5059422d468983a328f218b9172333c7.jpg",
            "https://i.pinimg.com/736x/0e/35/1d/0e351d3b781794b57ca87bbee4eacb06.jpg",
            "https://i.pinimg.com/736x/15/e0/88/15e088fc8d028769b7e1c1351900161c.jpg",
            "https://i.pinimg.com/736x/29/7d/68/297d68c6a203d565a92231ea71747c71.jpg",
            "https://i.pinimg.com/736x/ca/4d/3f/ca4d3f6ce69e34592c37a9dece595251.jpg",
            "https://i.pinimg.com/736x/1a/e9/a1/1ae9a14b26f30113e45a3d1443f496fe.jpg",
            "https://i.pinimg.com/736x/7d/de/5c/7dde5cfc73e31914cdfad78e948b4b67.jpg",
            "https://i.pinimg.com/736x/42/3e/2e/423e2e849831d1f3a7b2e295980748b7.jpg",
        ]
    }
]

def download_images_for_food(food_name, image_urls):
    """Télécharge les images pour un aliment donné"""
    downloaded_paths = []
    
    for i, url in enumerate(image_urls):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Créer un nom de fichier unique
                file_extension = url.split('.')[-1] if '.' in url else 'jpg'
                filename = f"{food_name.lower().replace(' ', '_')}_{i+1}.{file_extension}"
                filepath = os.path.join(MEDIA_FOLDER, filename)
                
                with open(filepath, "wb") as f:
                    f.write(response.content)
                
                downloaded_paths.append(filepath)
            
        except Exception as e:
            print(f"Erreur lors du téléchargement de {url}: {e}")
    
    return downloaded_paths

class AllergyDetectionEngine:
    """Moteur de détection d'allergies"""
    
    @staticmethod
    def calculate_allergy_score(user_id, food_id, days_back=30):
        """Calcule le score de risque allergique pour un aliment"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Récupérer les repas contenant cet aliment
        meals = meal_dao.get_user_meals(user_id, start_date.isoformat(), end_date.isoformat())
        food_meals = [meal for meal in meals if meal[2] == food_id]  # food_id est à l'index 2
        
        if not food_meals:
            return 0
        
        # Récupérer les symptômes dans la même période
        symptoms = symptom_dao.get_user_symptoms(user_id, start_date.isoformat(), end_date.isoformat())
        
        symptom_after_food_count = 0
        total_consumptions = len(food_meals)
        
        for meal in food_meals:
            meal_time = datetime.fromisoformat(meal[3])  # meal_time est à l'index 3
            
            # Chercher des symptômes dans les 2h à 48h après le repas
            for symptom in symptoms:
                symptom_time = datetime.fromisoformat(symptom[4])  # occurrence_time est à l'index 4
                time_diff = symptom_time - meal_time
                
                if timedelta(hours=2) <= time_diff <= timedelta(hours=48):
                    symptom_after_food_count += 1
                    break  # Un symptôme par repas maximum
        
        # Calcul du score de risque
        if total_consumptions == 0:
            return 0
        
        risk_score = (symptom_after_food_count / total_consumptions) * 100
        return round(risk_score, 2)
    
    @staticmethod
    def detect_potential_allergies(user_id, threshold=30):
        """Détecte les allergies potentielles pour un utilisateur"""
        foods = food_dao.get_all_foods()
        potential_allergies = []
        
        for food in foods:
            food_id = food[0]
            food_name = food[1]
            
            score = AllergyDetectionEngine.calculate_allergy_score(user_id, food_id)
            
            if score >= threshold:
                potential_allergies.append({
                    'food_id': food_id,
                    'food_name': food_name,
                    'risk_score': score,
                    'recommendation': 'Éviter cet aliment et consulter un médecin'
                })
        
        return sorted(potential_allergies, key=lambda x: x['risk_score'], reverse=True)

# Routes API

@app.route('/api/init-data', methods=['POST'])
def init_base_data():
    """Initialise les données de base avec les nourritures camerounaises"""
    try:
        loaded_foods = []
        
        for food_data in CAMEROON_FOODS_DATA:
            # Télécharger les images
            image_paths = download_images_for_food(food_data['name'], food_data.get('image_urls', []))
            image_path = image_paths[0] if image_paths else None
            
            # Créer l'aliment en base
            food_id = food_dao.create_food(
                name=food_data['name'],
                category=food_data['category'],
                ingredients=food_data['ingredients'],
                image_path=image_path,
                is_base_food=True
            )
            
            loaded_foods.append({
                'id': food_id,
                'name': food_data['name'],
                'images_downloaded': len(image_paths)
            })
        
        return jsonify({
            'success': True,
            'message': 'Données de base initialisées avec succès',
            'foods_loaded': loaded_foods
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de l\'initialisation: {str(e)}'
        }), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    """Créer un nouvel utilisateur"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'email' not in data:
        return jsonify({'error': 'Username et email requis'}), 400
    
    user_id = user_dao.create_user(data['username'], data['email'])
    
    if user_id:
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'Utilisateur créé avec succès'
        })
    else:
        return jsonify({'error': 'Utilisateur déjà existant'}), 409

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Récupérer les informations d'un utilisateur"""
    user = user_dao.get_user(user_id)
    
    if user:
        return jsonify({
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'created_at': user[3]
        })
    else:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404

@app.route('/api/foods', methods=['GET'])
def get_foods():
    """Récupérer tous les aliments avec leurs images principales"""
    foods = food_dao.get_all_foods()
    
    foods_list = []
    for food in foods:
        food_data = {
            'id': food[0],
            'name': food[1],
            'category': food[2],
            'ingredients': food[3],
            'image_path': food[4],
            'is_base_food': bool(food[5]),
            'image_url': None
        }
        
        # Récupérer l'image principale si elle existe
        try:
            with db_dao.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT file_path FROM food_images 
                    WHERE food_id = ? AND is_primary = 1
                    LIMIT 1
                ''', (food[0],))
                
                primary_image = cursor.fetchone()
                if primary_image and primary_image[0]:
                    filename = os.path.basename(primary_image[0])
                    food_data['image_url'] = f"/api/media/{filename}"
        except Exception as e:
            print(f"Erreur lors de la récupération de l'image principale: {e}")
        
        foods_list.append(food_data)
    
    return jsonify({'foods': foods_list})
@app.route('/api/foods', methods=['POST'])
def create_food():
    """Créer un nouvel aliment avec téléchargement d'image optionnel"""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Nom de l\'aliment requis'}), 400
    
    # Gérer le téléchargement d'image si une URL est fournie
    image_path = None
    image_download_info = None
    
    if 'image_url' in data and data['image_url']:
        try:
            # Télécharger l'image depuis l'URL
            result = image_manager.download_and_save_image(
                image_url=data['image_url'],
                food_id=None,  # Sera mis à jour après création de l'aliment
                food_name=data['name'],
                is_primary=True
            )
            
            if result['success']:
                image_path = result['file_path']
                image_download_info = {
                    'downloaded': True,
                    'original_url': data['image_url'],
                    'local_path': result['file_path'],
                    'file_size': result.get('file_size', 0)
                }
            else:
                image_download_info = {
                    'downloaded': False,
                    'error': result['error'],
                    'original_url': data['image_url']
                }
        except Exception as e:
            image_download_info = {
                'downloaded': False,
                'error': str(e),
                'original_url': data['image_url']
            }
    
    # Créer l'aliment en base
    food_id = food_dao.create_food(
        name=data['name'],
        category=data.get('category', ''),
        ingredients=data.get('ingredients', ''),
        image_path=image_path,
        is_base_food=data.get('is_base_food', False)
    )
    
    # Si l'image a été téléchargée avec succès, mettre à jour avec le food_id
    if image_path and image_download_info and image_download_info['downloaded']:
        try:
            # Enregistrer l'image dans la table images si elle existe
            with db_dao.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO food_images (food_id, file_path, original_url, is_primary, file_size)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    food_id, 
                    image_path, 
                    data['image_url'], 
                    True, 
                    image_download_info.get('file_size', 0)
                ))
                conn.commit()
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de l'image en base: {e}")
    
    # Préparer la réponse
    response_data = {
        'success': True,
        'food_id': food_id,
        'message': 'Aliment créé avec succès'
    }
    
    # Ajouter les informations sur l'image si une URL était fournie
    if 'image_url' in data:
        response_data['image_download'] = image_download_info
        if image_path:
            response_data['image_url'] = f"/api/media/{os.path.basename(image_path)}"
    
    return jsonify(response_data)
@app.route('/api/foods/<int:food_id>', methods=['GET'])
def get_food_detail(food_id):
    """Récupérer les détails d'un aliment avec ses images"""
    food = food_dao.get_food(food_id)
    
    if not food:
        return jsonify({'error': 'Aliment non trouvé'}), 404
    
    # Récupérer les images associées
    images = []
    try:
        with db_dao.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, file_path, original_url, is_primary, file_size, created_at
                FROM food_images 
                WHERE food_id = ?
                ORDER BY is_primary DESC, created_at DESC
            ''', (food_id,))
            
            image_records = cursor.fetchall()
            
            for img in image_records:
                # Construire l'URL accessible
                filename = os.path.basename(img[1]) if img[1] else None
                image_url = f"/api/media/{filename}" if filename else None
                
                images.append({
                    'id': img[0],
                    'file_path': img[1],
                    'image_url': image_url,
                    'original_url': img[2],
                    'is_primary': bool(img[3]),
                    'file_size': img[4],
                    'created_at': img[5]
                })
    except Exception as e:
        print(f"Erreur lors de la récupération des images: {e}")
    
    return jsonify({
        'id': food[0],
        'name': food[1],
        'category': food[2],
        'ingredients': food[3],
        'image_path': food[4],
        'is_base_food': bool(food[5]),
        'images': images,
        'primary_image_url': images[0]['image_url'] if images and images[0]['is_primary'] else None
    })

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Modifier les informations d'un utilisateur"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Données requises'}), 400
    
    # Vérifier que l'utilisateur existe
    if not user_dao.user_exists(user_id):
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    # Extraire les champs à modifier
    username = data.get('username')
    email = data.get('email')
    
    if not username and not email:
        return jsonify({'error': 'Au moins un champ à modifier doit être fourni (username ou email)'}), 400
    
    # Effectuer la mise à jour
    success = user_dao.update_user(user_id, username, email)
    
    if success:
        # Récupérer les données mises à jour
        updated_user = user_dao.get_user(user_id)
        return jsonify({
            'success': True,
            'message': 'Utilisateur mis à jour avec succès',
            'user': {
                'id': updated_user[0],
                'username': updated_user[1],
                'email': updated_user[2],
                'created_at': updated_user[3]
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Échec de la mise à jour (email ou nom d\'utilisateur déjà utilisé)'
        }), 409

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Supprimer un utilisateur et toutes ses données"""
    # Vérifier que l'utilisateur existe
    user = user_dao.get_user(user_id)
    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    # Demander confirmation (optionnel - via paramètre)
    confirm = request.args.get('confirm', '').lower()
    if confirm != 'true':
        return jsonify({
            'error': 'Suppression non confirmée',
            'message': 'Ajoutez ?confirm=true pour confirmer la suppression',
            'warning': 'Cette action supprimera définitivement toutes les données de l\'utilisateur'
        }), 400
    
    # Effectuer la suppression
    success = user_dao.delete_user(user_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': f'Utilisateur {user[1]} supprimé avec succès',
            'deleted_user': {
                'id': user[0],
                'username': user[1],
                'email': user[2]
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Échec de la suppression de l\'utilisateur'
        }), 500

@app.route('/api/users/<int:user_id>/stats', methods=['GET'])
def get_user_deletion_stats(user_id):
    """Obtenir les statistiques avant suppression d'un utilisateur"""
    if not user_dao.user_exists(user_id):
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    with db_dao.get_connection() as conn:
        cursor = conn.cursor()
        
        # Compter les données associées
        cursor.execute("SELECT COUNT(*) FROM meals WHERE user_id = ?", (user_id,))
        meals_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM symptoms WHERE user_id = ?", (user_id,))
        symptoms_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM weekly_plans WHERE user_id = ?", (user_id,))
        plans_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM buffet_events WHERE created_by = ?", (user_id,))
        buffets_count = cursor.fetchone()[0]
    
    user = user_dao.get_user(user_id)
    
    return jsonify({
        'user_id': user_id,
        'username': user[1],
        'data_summary': {
            'meals_recorded': meals_count,
            'symptoms_logged': symptoms_count,
            'weekly_plans': plans_count,
            'buffet_events_created': buffets_count,
            'total_records': meals_count + symptoms_count + plans_count + buffets_count
        },
        'warning': 'La suppression de cet utilisateur effacera définitivement toutes ces données'
    })

# 3. Route pour récupérer tous les utilisateurs avec pagination
@app.route('/api/users', methods=['GET'])
def get_all_users():
    """Récupérer tous les utilisateurs avec pagination optionnelle"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '').strip()
        
        with db_dao.get_connection() as conn:
            cursor = conn.cursor()
            
            # Requête de base
            base_query = "SELECT * FROM users"
            count_query = "SELECT COUNT(*) FROM users"
            params = []
            
            # Ajouter la recherche si fournie
            if search:
                base_query += " WHERE username LIKE ? OR email LIKE ?"
                count_query += " WHERE username LIKE ? OR email LIKE ?"
                params = [f"%{search}%", f"%{search}%"]
            
            # Compter le total
            cursor.execute(count_query, params)
            total_users = cursor.fetchone()[0]
            
            # Calculer la pagination
            offset = (page - 1) * per_page
            base_query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([per_page, offset])
            
            # Récupérer les utilisateurs
            cursor.execute(base_query, params)
            users = cursor.fetchall()
            
            users_list = []
            for user in users:
                users_list.append({
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'created_at': user[3]
                })
            
            return jsonify({
                'users': users_list,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_users': total_users,
                    'total_pages': (total_users + per_page - 1) // per_page,
                    'has_next': page * per_page < total_users,
                    'has_prev': page > 1
                },
                'search': search if search else None
            })
            
    except ValueError:
        return jsonify({'error': 'Paramètres de pagination invalides'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/api/foods/search', methods=['GET'])
def search_foods():
    """Rechercher des aliments"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Paramètre de recherche requis'}), 400
    
    foods = food_dao.search_foods(query)
    
    foods_list = []
    for food in foods:
        foods_list.append({
            'id': food[0],
            'name': food[1],
            'category': food[2],
            'ingredients': food[3],
            'image_path': food[4]
        })
    
    return jsonify({'foods': foods_list})

@app.route('/api/meals', methods=['POST'])
def create_meal():
    """Enregistrer un repas"""
    data = request.get_json()
    
    required_fields = ['user_id', 'food_id', 'meal_time', 'quantity']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Tous les champs requis doivent être fournis'}), 400
    
    meal_id = meal_dao.create_meal(
        user_id=data['user_id'],
        food_id=data['food_id'],
        meal_time=data['meal_time'],
        quantity=data['quantity'],
        notes=data.get('notes')
    )
    
    return jsonify({
        'success': True,
        'meal_id': meal_id,
        'message': 'Repas enregistré avec succès'
    })

@app.route('/api/users/<int:user_id>/meals', methods=['GET'])
def get_user_meals(user_id):
    """Récupérer les repas d'un utilisateur"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    meals = meal_dao.get_user_meals(user_id, start_date, end_date)
    
    meals_list = []
    for meal in meals:
        meals_list.append({
            'id': meal[0],
            'user_id': meal[1],
            'food_id': meal[2],
            'meal_time': meal[3],
            'quantity': meal[4],
            'notes': meal[5],
            'food_name': meal[6],
            'ingredients': meal[7]
        })
    
    return jsonify({'meals': meals_list})

@app.route('/api/symptoms', methods=['POST'])
def create_symptom():
    """Enregistrer un symptôme"""
    data = request.get_json()
    
    required_fields = ['user_id', 'symptom_type', 'severity', 'occurrence_time']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Tous les champs requis doivent être fournis'}), 400
    
    if not (1 <= data['severity'] <= 5):
        return jsonify({'error': 'La sévérité doit être entre 1 et 5'}), 400
    
    symptom_id = symptom_dao.create_symptom(
        user_id=data['user_id'],
        symptom_type=data['symptom_type'],
        severity=data['severity'],
        occurrence_time=data['occurrence_time'],
        description=data.get('description')
    )
    
    return jsonify({
        'success': True,
        'symptom_id': symptom_id,
        'message': 'Symptôme enregistré avec succès'
    })

@app.route('/api/users/<int:user_id>/symptoms', methods=['GET'])
def get_user_symptoms(user_id):
    """Récupérer les symptômes d'un utilisateur"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    symptoms = symptom_dao.get_user_symptoms(user_id, start_date, end_date)
    
    symptoms_list = []
    for symptom in symptoms:
        symptoms_list.append({
            'id': symptom[0],
            'user_id': symptom[1],
            'symptom_type': symptom[2],
            'severity': symptom[3],
            'occurrence_time': symptom[4],
            'description': symptom[5]
        })
    
    return jsonify({'symptoms': symptoms_list})

@app.route('/api/users/<int:user_id>/allergy-analysis', methods=['GET'])
def analyze_allergies(user_id):
    """Analyser les allergies potentielles d'un utilisateur"""
    threshold = float(request.args.get('threshold', 30))
    
    potential_allergies = AllergyDetectionEngine.detect_potential_allergies(user_id, threshold)
    
    return jsonify({
        'user_id': user_id,
        'analysis_date': datetime.now().isoformat(),
        'threshold_used': threshold,
        'potential_allergies': potential_allergies,
        'total_detected': len(potential_allergies)
    })

@app.route('/api/users/<int:user_id>/food-risk/<int:food_id>', methods=['GET'])
def get_food_risk_score(user_id, food_id):
    """Calculer le score de risque pour un aliment spécifique"""
    days_back = int(request.args.get('days', 30))
    
    score = AllergyDetectionEngine.calculate_allergy_score(user_id, food_id, days_back)
    food = food_dao.get_food(food_id)
    
    if not food:
        return jsonify({'error': 'Aliment non trouvé'}), 404
    
    return jsonify({
        'user_id': user_id,
        'food_id': food_id,
        'food_name': food[1],
        'risk_score': score,
        'days_analyzed': days_back,
        'risk_level': 'Élevé' if score >= 30 else 'Modéré' if score >= 15 else 'Faible'
    })

# Module de planification hebdomadaire
@app.route('/api/users/<int:user_id>/weekly-plan', methods=['POST'])
def create_weekly_plan(user_id):
    """Créer un plan alimentaire hebdomadaire"""
    data = request.get_json()
    user_id = int(request.view_args['user_id'])
    
    if not data or 'week_start_date' not in data or 'meals' not in data:
        return jsonify({'error': 'Date de début et repas requis'}), 400
    
    with db_dao.get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            for meal in data['meals']:
                cursor.execute('''
                    INSERT INTO weekly_plans 
                    (user_id, week_start_date, day_of_week, meal_type, food_id, planned_quantity)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    data['week_start_date'],
                    meal['day_of_week'],
                    meal['meal_type'],
                    meal['food_id'],
                    meal.get('planned_quantity', 1)
                ))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Plan hebdomadaire créé avec succès'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/weekly-plan', methods=['GET'])
def get_weekly_plan(user_id):
    """Récupérer le plan alimentaire hebdomadaire"""
    week_start = request.args.get('week_start_date')
    
    with db_dao.get_connection() as conn:
        cursor = conn.cursor()
        
        query = '''
            SELECT wp.*, f.name as food_name, f.category, f.ingredients
            FROM weekly_plans wp
            JOIN foods f ON wp.food_id = f.id
            WHERE wp.user_id = ?
        '''
        params = [user_id]
        
        if week_start:
            query += " AND wp.week_start_date = ?"
            params.append(week_start)
        
        query += " ORDER BY wp.day_of_week, wp.meal_type"
        
        cursor.execute(query, params)
        plans = cursor.fetchall()
        
        weekly_plan = []
        for plan in plans:
            weekly_plan.append({
                'id': plan[0],
                'day_of_week': plan[3],
                'meal_type': plan[4],
                'food_id': plan[5],
                'planned_quantity': plan[6],
                'food_name': plan[7],
                'category': plan[8],
                'ingredients': plan[9]
            })
        
        return jsonify({
            'user_id': user_id,
            'week_start_date': week_start,
            'weekly_plan': weekly_plan
        })

# Module de gestion de buffet
@app.route('/api/buffet-events', methods=['POST'])
def create_buffet_event():
    """Créer un événement buffet"""
    data = request.get_json()
    
    required_fields = ['event_name', 'event_date', 'estimated_guests', 'created_by']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Tous les champs requis doivent être fournis'}), 400
    
    with db_dao.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO buffet_events (event_name, event_date, estimated_guests, created_by)
            VALUES (?, ?, ?, ?)
        ''', (
            data['event_name'],
            data['event_date'],
            data['estimated_guests'],
            data['created_by']
        ))
        
        buffet_id = cursor.lastrowid
        
        # Ajouter les aliments du buffet si fournis
        if 'foods' in data:
            for food_item in data['foods']:
                cursor.execute('''
                    INSERT INTO buffet_foods (buffet_id, food_id, planned_quantity, unit)
                    VALUES (?, ?, ?, ?)
                ''', (
                    buffet_id,
                    food_item['food_id'],
                    food_item.get('planned_quantity', 1),
                    food_item.get('unit', 'portions')
                ))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'buffet_id': buffet_id,
            'message': 'Événement buffet créé avec succès'
        })

@app.route('/api/buffet-events/<int:buffet_id>', methods=['GET'])
def get_buffet_event(buffet_id):
    """Récupérer les détails d'un événement buffet"""
    with db_dao.get_connection() as conn:
        cursor = conn.cursor()
        
        # Récupérer l'événement
        cursor.execute('''
            SELECT be.*, u.username 
            FROM buffet_events be
            JOIN users u ON be.created_by = u.id
            WHERE be.id = ?
        ''', (buffet_id,))
        
        event = cursor.fetchone()
        
        if not event:
            return jsonify({'error': 'Événement non trouvé'}), 404
        
        # Récupérer les aliments du buffet
        cursor.execute('''
            SELECT bf.*, f.name as food_name, f.category, f.ingredients
            FROM buffet_foods bf
            JOIN foods f ON bf.food_id = f.id
            WHERE bf.buffet_id = ?
        ''', (buffet_id,))
        
        foods = cursor.fetchall()
        
        buffet_foods = []
        for food in foods:
            buffet_foods.append({
                'id': food[0],
                'food_id': food[2],
                'planned_quantity': food[3],
                'unit': food[4],
                'food_name': food[5],
                'category': food[6],
                'ingredients': food[7]
            })
        
        return jsonify({
            'id': event[0],
            'event_name': event[1],
            'event_date': event[2],
            'estimated_guests': event[3],
            'created_by': event[4],
            'creator_username': event[5],
            'foods': buffet_foods
        })

@app.route('/api/buffet-events', methods=['GET'])
def get_buffet_events():
    """Récupérer tous les événements buffet"""
    with db_dao.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT be.*, u.username 
            FROM buffet_events be
            JOIN users u ON be.created_by = u.id
            ORDER BY be.event_date DESC
        ''')
        
        events = cursor.fetchall()
        
        events_list = []
        for event in events:
            events_list.append({
                'id': event[0],
                'event_name': event[1],
                'event_date': event[2],
                'estimated_guests': event[3],
                'created_by': event[4],
                'creator_username': event[5]
            })
        
        return jsonify({'buffet_events': events_list})

@app.route('/api/buffet-events/<int:buffet_id>/calculate-quantities', methods=['GET'])
def calculate_buffet_quantities(buffet_id):
    """Calculer les quantités recommandées pour un buffet"""
    with db_dao.get_connection() as conn:
        cursor = conn.cursor()
        
        # Récupérer l'événement
        cursor.execute('SELECT * FROM buffet_events WHERE id = ?', (buffet_id,))
        event = cursor.fetchone()
        
        if not event:
            return jsonify({'error': 'Événement non trouvé'}), 404
        
        estimated_guests = event[3]
        
        # Récupérer les aliments du buffet
        cursor.execute('''
            SELECT bf.*, f.name as food_name, f.category
            FROM buffet_foods bf
            JOIN foods f ON bf.food_id = f.id
            WHERE bf.buffet_id = ?
        ''', (buffet_id,))
        
        foods = cursor.fetchall()
        
        recommendations = []
        for food in foods:
            planned_quantity = food[3]
            food_name = food[5]
            category = food[6]
            
            # Calculs basiques selon la catégorie
            if category == 'Plat principal':
                recommended_per_person = 1.2  # 1.2 portions par personne
            elif category in ['Accompagnement', 'Légume']:
                recommended_per_person = 0.8
            elif category in ['Dessert', 'Boisson']:
                recommended_per_person = 1.0
            else:
                recommended_per_person = 1.0
            
            total_recommended = estimated_guests * recommended_per_person
            
            recommendations.append({
                'food_id': food[2],
                'food_name': food_name,
                'category': category,
                'planned_quantity': planned_quantity,
                'recommended_quantity': round(total_recommended, 1),
                'per_person': recommended_per_person,
                'unit': food[4]
            })
        
        return jsonify({
            'buffet_id': buffet_id,
            'estimated_guests': estimated_guests,
            'recommendations': recommendations
        })

# Routes utilitaires et statistiques
@app.route('/api/users/<int:user_id>/dashboard', methods=['GET'])
def get_user_dashboard(user_id):
    """Tableau de bord utilisateur avec statistiques"""
    try:
        # Période d'analyse (30 derniers jours par défaut)
        days_back = int(request.args.get('days', 30))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Statistiques des repas
        meals = meal_dao.get_user_meals(user_id, start_date.isoformat(), end_date.isoformat())
        total_meals = len(meals)
        
        # Statistiques des symptômes
        symptoms = symptom_dao.get_user_symptoms(user_id, start_date.isoformat(), end_date.isoformat())
        total_symptoms = len(symptoms)
        
        # Analyse des allergies
        potential_allergies = AllergyDetectionEngine.detect_potential_allergies(user_id)
        high_risk_foods = [allergy for allergy in potential_allergies if allergy['risk_score'] >= 50]
        
        # Aliments les plus consommés
        food_consumption = defaultdict(int)
        for meal in meals:
            food_consumption[meal[6]] += 1  # food_name
        
        most_consumed = sorted(food_consumption.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return jsonify({
            'user_id': user_id,
            'period_days': days_back,
            'statistics': {
                'total_meals': total_meals,
                'total_symptoms': total_symptoms,
                'avg_meals_per_day': round(total_meals / days_back, 1),
                'avg_symptoms_per_day': round(total_symptoms / days_back, 1)
            },
            'allergy_analysis': {
                'total_potential_allergies': len(potential_allergies),
                'high_risk_foods': len(high_risk_foods),
                'top_risks': potential_allergies[:3]
            },
            'consumption_patterns': {
                'most_consumed_foods': [{'food': food, 'count': count} for food, count in most_consumed]
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérification de l'état de l'API"""
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'database': 'Connected'
    })

@app.route('/api/export/<int:user_id>/data', methods=['GET'])
def export_user_data(user_id):
    """Exporter toutes les données d'un utilisateur"""
    try:
        # Récupérer toutes les données
        user = user_dao.get_user(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        meals = meal_dao.get_user_meals(user_id)
        symptoms = symptom_dao.get_user_symptoms(user_id)
        potential_allergies = AllergyDetectionEngine.detect_potential_allergies(user_id)
        
        export_data = {
            'user_info': {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'created_at': user[3]
            },
            'meals': [
                {
                    'id': meal[0],
                    'food_name': meal[6],
                    'meal_time': meal[3],
                    'quantity': meal[4],
                    'notes': meal[5],
                    'ingredients': meal[7]
                } for meal in meals
            ],
            'symptoms': [
                {
                    'id': symptom[0],
                    'symptom_type': symptom[2],
                    'severity': symptom[3],
                    'occurrence_time': symptom[4],
                    'description': symptom[5]
                } for symptom in symptoms
            ],
            'allergy_analysis': potential_allergies,
            'export_date': datetime.now().isoformat()
        }
        
        return jsonify(export_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Routes de recommandations intelligentes
@app.route('/api/users/<int:user_id>/recommendations', methods=['GET'])
def get_recommendations(user_id):
    """Obtenir des recommandations personnalisées"""
    try:
        # Analyser les habitudes alimentaires
        meals = meal_dao.get_user_meals(user_id)
        symptoms = symptom_dao.get_user_symptoms(user_id)
        potential_allergies = AllergyDetectionEngine.detect_potential_allergies(user_id)
        
        recommendations = []
        
        # Recommandations basées sur les allergies détectées
        if potential_allergies:
            high_risk = [a for a in potential_allergies if a['risk_score'] > 50]
            if high_risk:
                recommendations.append({
                    'type': 'allergy_warning',
                    'priority': 'high',
                    'title': 'Allergies potentielles détectées',
                    'message': f'Nous avons détecté {len(high_risk)} aliment(s) à risque élevé. Consultez un médecin.',
                    'foods': [food['food_name'] for food in high_risk[:3]]
                })
        
        # Recommandations de diversification
        food_variety = defaultdict(int)
        for meal in meals[-30:]:  # 30 derniers repas
            food_variety[meal[6]] += 1
        
        if len(food_variety) < 5:
            recommendations.append({
                'type': 'diversification',
                'priority': 'medium',
                'title': 'Diversifiez votre alimentation',
                'message': 'Essayez d\'inclure plus de variété dans vos repas pour une meilleure santé.',
                'suggestion': 'Explorez de nouveaux aliments de notre base de données'
            })
        
        # Recommandations basées sur les symptômes fréquents
        if len(symptoms) > 10:  # Plus de 10 symptômes
            symptom_types = defaultdict(int)
            for symptom in symptoms:
                symptom_types[symptom[2]] += 1
            
            most_common = max(symptom_types.items(), key=lambda x: x[1])
            recommendations.append({
                'type': 'symptom_pattern',
                'priority': 'medium',
                'title': 'Symptômes récurrents détectés',
                'message': f'Vous avez rapporté {most_common[1]} fois le symptôme "{most_common[0]}". Surveillez vos habitudes alimentaires.',
                'action': 'Tenez un journal plus détaillé'
            })
        
        return jsonify({
            'user_id': user_id,
            'recommendations': recommendations,
            'total_recommendations': len(recommendations),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# 6. Nouvelles routes pour la gestion des images
@app.route('/api/foods/<int:food_id>/images', methods=['POST'])
def add_food_image(food_id):
    image_manager = ImageManager()
    """Ajouter une image à un aliment existant"""
    data = request.get_json()
    
    if not data or 'image_url' not in data:
        return jsonify({'error': 'URL de l\'image requise'}), 400
    
    # Vérifier que l'aliment existe
    food = food_dao.get_food(food_id)
    if not food:
        return jsonify({'error': 'Aliment non trouvé'}), 404
    # Télécharger l'image
    result = image_manager.download_and_save_image(
        image_url=data['image_url'],
        food_id=food_id,
        food_name=food[1],  # nom de l'aliment
        is_primary=data.get('is_primary', False)
    )
    
    if result['success']:
        return jsonify({
            'success': True,
            'message': 'Image ajoutée avec succès',
            'image_data': result
        })
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 400

@app.route('/api/foods/<int:food_id>/images', methods=['GET'])
def get_food_images(food_id):
    """Récupérer toutes les images d'un aliment"""
    food = food_dao.get_food(food_id)
    if not food:
        return jsonify({'error': 'Aliment non trouvé'}), 404
    
    images = image_manager.get_food_images(food_id)
    
    return jsonify({
        'food_id': food_id,
        'food_name': food[1],
        'images': images,
        'total_images': len(images)
    })

@app.route('/api/images/<int:image_id>/primary', methods=['PUT'])
def set_primary_image(image_id):
    """Définir une image comme image principale"""
    success = image_manager.set_primary_image(image_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Image définie comme principale'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Image non trouvée'
        }), 404

@app.route('/api/images/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Supprimer une image"""
    success = image_manager.delete_image(image_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Image supprimée avec succès'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Impossible de supprimer l\'image'
        }), 404

@app.route('/api/media/<path:filename>', methods=['GET'])
def serve_media(filename):
    """Servir les fichiers media"""
    try:
        return send_from_directory(MEDIA_FOLDER, filename)
    except FileNotFoundError:
        return jsonify({'error': 'Fichier non trouvé'}), 404

if __name__ == '__main__':
    # Créer le dossier media s'il n'existe pas
    if not os.path.exists('media'):
        os.makedirs('media')
    
    print("🚀 API de Détection d'Allergies Alimentaires")
    print("📋 Fonctionnalités disponibles:")
    print("   • Gestion des utilisateurs et aliments")
    print("   • Journal alimentaire et suivi des symptômes")
    print("   • Détection intelligente d'allergies")
    print("   • Planification hebdomadaire des repas")
    print("   • Gestion de buffets pour événements")
    print("   • Recommandations personnalisées")
    print("🔗 Utilisez Postman pour tester les endpoints")
    print("📊 Initialisez les données avec POST /api/init-data")
    
    app.run(debug=True, host='0.0.0.0', port=5000)