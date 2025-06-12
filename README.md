# 🍽️ API de Détection d'Allergies Alimentaires

Une API REST complète pour le suivi alimentaire et la détection intelligente d'allergies, avec un focus sur la cuisine camerounaise.

## 📋 Table des matières

- [Fonctionnalités](#fonctionnalités)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Endpoints de l'API](#endpoints-de-lapi)
- [Tests avec Postman](#tests-avec-postman)
- [Exemples d'utilisation](#exemples-dutilisation)
- [Structure de la base de données](#structure-de-la-base-de-données)
- [Algorithme de détection](#algorithme-de-détection)

## 🚀 Fonctionnalités

### 👥 Gestion des utilisateurs
- Création, lecture, modification et suppression d'utilisateurs
- Pagination et recherche
- Statistiques avant suppression
- Export des données utilisateur

### 🍲 Gestion des aliments
- Base de données pré-remplie avec des aliments camerounais
- Recherche d'aliments par nom et ingrédients
- Gestion des images d'aliments
- Catégorisation des aliments

### 📝 Journal alimentaire
- Enregistrement des repas avec quantités
- Suivi des symptômes avec échelle de sévérité
- Filtrage par dates
- Historique complet

### 🔬 Détection d'allergies
- Algorithme intelligent d'analyse des corrélations
- Score de risque personnalisé
- Recommandations basées sur les patterns
- Analyse temporelle des symptômes

### 📅 Planification hebdomadaire
- Création de menus personnalisés
- Planification par jour et type de repas
- Intégration avec l'analyse d'allergies

### 🎉 Gestion de buffets
- Organisation d'événements
- Calcul automatique des quantités
- Gestion des invités
- Recommandations par catégorie d'aliments

## 💻 Installation

### Prérequis
- Python 3.8+
- pip
- SQLite3

### Installation des dépendances

```bash
pip install flask flask-cors requests pillow
```

### Structure du projet

```
allergy-detection-api/
├── app.py                 # API principale
├── dao/
│   ├── db_dao.py         # Gestion base de données
│   ├── user_dao.py       # DAO utilisateurs
│   ├── food_dao.py       # DAO aliments
│   ├── meal_dao.py       # DAO repas
│   └── symptom_dao.py    # DAO symptômes
├── services/
│   ├── allergy_engine.py # Moteur de détection
│   └── image_manager.py  # Gestion des images
├── data/
│   └── cameroon_foods.py # Données aliments camerounais
├── media/                # Dossier des images
└── database.db          # Base de données SQLite
```

## ⚙️ Configuration

### Variables d'environnement

```bash
# Optionnel - Configuration par défaut dans le code
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_PATH=database.db
MEDIA_FOLDER=media
```

### Initialisation de la base de données

L'API crée automatiquement la base de données au premier lancement. Pour initialiser avec les données camerounaises :

```bash
POST /api/init-data
```

## 🎯 Utilisation

### Démarrage du serveur

```bash
python app.py
```

L'API sera accessible sur `http://localhost:5000`

### Vérification de santé

```bash
GET /api/health
```

## 🔗 Endpoints de l'API

### 👥 Utilisateurs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/users` | Créer un utilisateur |
| `GET` | `/api/users` | Lister tous les utilisateurs (avec pagination) |
| `GET` | `/api/users/{id}` | Obtenir un utilisateur |
| `PUT` | `/api/users/{id}` | Modifier un utilisateur |
| `DELETE` | `/api/users/{id}?confirm=true` | Supprimer un utilisateur |
| `GET` | `/api/users/{id}/stats` | Statistiques avant suppression |
| `GET` | `/api/users/{id}/dashboard` | Tableau de bord utilisateur |

### 🍲 Aliments

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/init-data` | Initialiser les données de base |
| `GET` | `/api/foods` | Lister tous les aliments |
| `POST` | `/api/foods` | Créer un aliment |
| `GET` | `/api/foods/search?q={query}` | Rechercher des aliments |
| `POST` | `/api/foods/{id}/images` | Ajouter une image |
| `GET` | `/api/foods/{id}/images` | Images d'un aliment |

### 📝 Journal alimentaire

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/meals` | Enregistrer un repas |
| `GET` | `/api/users/{id}/meals` | Repas d'un utilisateur |
| `POST` | `/api/symptoms` | Enregistrer un symptôme |
| `GET` | `/api/users/{id}/symptoms` | Symptômes d'un utilisateur |

### 🔬 Analyse d'allergies

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/users/{id}/allergy-analysis` | Analyse complète |
| `GET` | `/api/users/{id}/food-risk/{food_id}` | Risque pour un aliment |
| `GET` | `/api/users/{id}/recommendations` | Recommandations |

### 📅 Planification

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/users/{id}/weekly-plan` | Créer un plan hebdomadaire |
| `GET` | `/api/users/{id}/weekly-plan` | Obtenir le plan |

### 🎉 Buffets

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/buffet-events` | Créer un événement |
| `GET` | `/api/buffet-events` | Lister les événements |
| `GET` | `/api/buffet-events/{id}` | Détails d'un événement |
| `GET` | `/api/buffet-events/{id}/calculate-quantities` | Calcul des quantités |

# Simulation de Tests Postman - API Alimentaire

## Scénario de Test : Utilisateur "Marie Dubois" - Suivi Alimentaire Complet

### Variables d'environnement Postman
```
BASE_URL = http://localhost:5000
USER_ID = (à définir après création)
FOOD_ID = (à définir après création)
MEAL_ID = (à définir après création)
BUFFET_ID = (à définir après création)
```

---

## 1. INITIALISATION DU SYSTÈME

### 1.1 Vérification de l'état de l'API
**GET** `{{BASE_URL}}/api/health`

**Réponse attendue :**
```json
{
  "status": "OK",
  "timestamp": "2025-06-12T10:00:00.000Z",
  "version": "1.0.0",
  "database": "Connected"
}
```

### 1.2 Initialisation des données de base
**POST** `{{BASE_URL}}/api/init-data`

**Réponse attendue :**
```json
{
  "success": true,
  "message": "Données de base initialisées avec succès",
  "foods_loaded": [
    {
      "id": 1,
      "name": "Ndolé",
      "images_downloaded": 2
    },
    {
      "id": 2,
      "name": "Poulet DG",
      "images_downloaded": 1
    }
  ]
}
```

---

## 2. GESTION DES UTILISATEURS

### 2.1 Création d'un utilisateur
**POST** `{{BASE_URL}}/api/users`

**Body (JSON) :**
```json
{
  "username": "marie_dubois",
  "email": "marie.dubois@email.com"
}
```

**Réponse attendue :**
```json
{
  "success": true,
  "user_id": 1,
  "message": "Utilisateur créé avec succès"
}
```
*Sauvegarder USER_ID = 1*

### 2.2 Récupération des informations utilisateur
**GET** `{{BASE_URL}}/api/users/{{USER_ID}}`

**Réponse attendue :**
```json
{
  "id": 1,
  "username": "marie_dubois",
  "email": "marie.dubois@email.com",
  "created_at": "2025-06-12T10:05:00.000Z"
}
```

### 2.3 Modification de l'utilisateur
**PUT** `{{BASE_URL}}/api/users/{{USER_ID}}`

**Body (JSON) :**
```json
{
  "email": "marie.dubois.updated@email.com"
}
```

**Réponse attendue :**
```json
{
  "success": true,
  "message": "Utilisateur mis à jour avec succès",
  "user": {
    "id": 1,
    "username": "marie_dubois",
    "email": "marie.dubois.updated@email.com",
    "created_at": "2025-06-12T10:05:00.000Z"
  }
}
```

### 2.4 Liste des utilisateurs avec pagination
**GET** `{{BASE_URL}}/api/users?page=1&per_page=5&search=marie`

**Réponse attendue :**
```json
{
  "users": [
    {
      "id": 1,
      "username": "marie_dubois",
      "email": "marie.dubois.updated@email.com",
      "created_at": "2025-06-12T10:05:00.000Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 5,
    "total_users": 1,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  },
  "search": "marie"
}
```

---

## 3. GESTION DES ALIMENTS

### 3.1 Récupération de tous les aliments
**GET** `{{BASE_URL}}/api/foods`

**Réponse attendue :**
```json
{
  "foods": [
    {
      "id": 1,
      "name": "Ndolé",
      "category": "Plat principal",
      "ingredients": "Feuilles de ndolé, arachides, poisson, viande",
      "image_path": "/media/images/ndole_1.jpg",
      "is_base_food": true,
      "image_url": "/api/media/ndole_1.jpg"
    }
  ]
}
```

### 3.2 Création d'un nouvel aliment avec image
**POST** `{{BASE_URL}}/api/foods`

**Body (JSON) :**
```json
{
  "name": "Salade de Marie",
  "category": "Entrée",
  "ingredients": "Laitue, tomates, concombre, avocat",
  "image_url": "https://example.com/salade.jpg",
  "is_base_food": false
}
```

**Réponse attendue :**
```json
{
  "success": true,
  "food_id": 15,
  "message": "Aliment créé avec succès",
  "image_download": {
    "downloaded": true,
    "original_url": "https://example.com/salade.jpg",
    "local_path": "/media/images/salade_de_marie_1.jpg",
    "file_size": 45230
  },
  "image_url": "/api/media/salade_de_marie_1.jpg"
}
```
*Sauvegarder FOOD_ID = 15*

### 3.3 Détails d'un aliment avec ses images
**GET** `{{BASE_URL}}/api/foods/{{FOOD_ID}}`

**Réponse attendue :**
```json
{
  "id": 15,
  "name": "Salade de Marie",
  "category": "Entrée",
  "ingredients": "Laitue, tomates, concombre, avocat",
  "image_path": "/media/images/salade_de_marie_1.jpg",
  "is_base_food": false,
  "images": [
    {
      "id": 1,
      "file_path": "/media/images/salade_de_marie_1.jpg",
      "image_url": "/api/media/salade_de_marie_1.jpg",
      "original_url": "https://example.com/salade.jpg",
      "is_primary": true,
      "file_size": 45230,
      "created_at": "2025-06-12T10:15:00.000Z"
    }
  ],
  "primary_image_url": "/api/media/salade_de_marie_1.jpg"
}
```

### 3.4 Recherche d'aliments
**GET** `{{BASE_URL}}/api/foods/search?q=salade`

**Réponse attendue :**
```json
{
  "foods": [
    {
      "id": 15,
      "name": "Salade de Marie",
      "category": "Entrée",
      "ingredients": "Laitue, tomates, concombre, avocat",
      "image_path": "/media/images/salade_de_marie_1.jpg"
    }
  ]
}
```

### 3.5 Ajout d'une image supplémentaire à un aliment
**POST** `{{BASE_URL}}/api/foods/{{FOOD_ID}}/images`

**Body (JSON) :**
```json
{
  "image_url": "https://example.com/salade2.jpg",
  "is_primary": false
}
```

**Réponse attendue :**
```json
{
  "success": true,
  "message": "Image ajoutée avec succès",
  "image_data": {
    "success": true,
    "file_path": "/media/images/salade_de_marie_2.jpg",
    "image_id": 2,
    "file_size": 38450
  }
}
```

---

## 4. ENREGISTREMENT DES REPAS

### 4.1 Enregistrement d'un repas du petit-déjeuner
**POST** `{{BASE_URL}}/api/meals`

**Body (JSON) :**
```json
{
  "user_id": 1,
  "food_id": 15,
  "meal_time": "2025-06-12T08:00:00.000Z",
  "quantity": 1,
  "notes": "Petit-déjeuner léger avec avocat"
}
```

**Réponse attendue :**
```json
{
  "success": true,
  "meal_id": 1,
  "message": "Repas enregistré avec succès"
}
```

### 4.2 Enregistrement d'un repas du déjeuner
**POST** `{{BASE_URL}}/api/meals`

**Body (JSON) :**
```json
{
  "user_id": 1,
  "food_id": 1,
  "meal_time": "2025-06-12T13:00:00.000Z",
  "quantity": 1.5,
  "notes": "Déjeuner copieux avec du ndolé"
}
```

### 4.3 Récupération des repas de l'utilisateur
**GET** `{{BASE_URL}}/api/users/{{USER_ID}}/meals?start_date=2025-06-12&end_date=2025-06-12`

**Réponse attendue :**
```json
{
  "meals": [
    {
      "id": 1,
      "user_id": 1,
      "food_id": 15,
      "meal_time": "2025-06-12T08:00:00.000Z",
      "quantity": 1,
      "notes": "Petit-déjeuner léger avec avocat",
      "food_name": "Salade de Marie",
      "ingredients": "Laitue, tomates, concombre, avocat"
    },
    {
      "id": 2,
      "user_id": 1,
      "food_id": 1,
      "meal_time": "2025-06-12T13:00:00.000Z",
      "quantity": 1.5,
      "notes": "Déjeuner copieux avec du ndolé",
      "food_name": "Ndolé",
      "ingredients": "Feuilles de ndolé, arachides, poisson, viande"
    }
  ]
}
```

---

## 5. ENREGISTREMENT DES SYMPTÔMES

### 5.1 Enregistrement d'un symptôme léger
**POST** `{{BASE_URL}}/api/symptoms`

**Body (JSON) :**
```json
{
  "user_id": 1,
  "symptom_type": "Ballonnements",
  "severity": 2,
  "occurrence_time": "2025-06-12T15:30:00.000Z",
  "description": "Légers ballonnements après le déjeuner"
}
```

**Réponse attendue :**
```json
{
  "success": true,
  "symptom_id": 1,
  "message": "Symptôme enregistré avec succès"
}
```

### 5.2 Enregistrement d'un symptôme plus sévère
**POST** `{{BASE_URL}}/api/symptoms`

**Body (JSON) :**
```json
{
  "user_id": 1,
  "symptom_type": "Nausées",
  "severity": 4,
  "occurrence_time": "2025-06-12T16:00:00.000Z",
  "description": "Nausées importantes 3h après le déjeuner"
}
```

### 5.3 Récupération des symptômes de l'utilisateur
**GET** `{{BASE_URL}}/api/users/{{USER_ID}}/symptoms?start_date=2025-06-12&end_date=2025-06-12`

**Réponse attendue :**
```json
{
  "symptoms": [
    {
      "id": 1,
      "user_id": 1,
      "symptom_type": "Ballonnements",
      "severity": 2,
      "occurrence_time": "2025-06-12T15:30:00.000Z",
      "description": "Légers ballonnements après le déjeuner"
    },
    {
      "id": 2,
      "user_id": 1,
      "symptom_type": "Nausées",
      "severity": 4,
      "occurrence_time": "2025-06-12T16:00:00.000Z",
      "description": "Nausées importantes 3h après le déjeuner"
    }
  ]
}
```

---

## 6. ANALYSE DES ALLERGIES

### 6.1 Analyse des allergies potentielles
**GET** `{{BASE_URL}}/api/users/{{USER_ID}}/allergy-analysis?threshold=20`

**Réponse attendue :**
```json
{
  "user_id": 1,
  "analysis_date": "2025-06-12T16:30:00.000Z",
  "threshold_used": 20,
  "potential_allergies": [
    {
      "food_id": 1,
      "food_name": "Ndolé",
      "risk_score": 35.5,
      "meal_count": 1,
      "symptom_count": 2,
      "avg_symptom_severity": 3.0,
      "symptoms_within_6h": 2
    }
  ],
  "total_detected": 1
}
```

### 6.2 Score de risque pour un aliment spécifique
**GET** `{{BASE_URL}}/api/users/{{USER_ID}}/food-risk/1?days=30`

**Réponse attendue :**
```json
{
  "user_id": 1,
  "food_id": 1,
  "food_name": "Ndolé",
  "risk_score": 35.5,
  "days_analyzed": 30,
  "risk_level": "Modéré"
}
```

---

## 7. PLANIFICATION HEBDOMADAIRE

### 7.1 Création d'un plan hebdomadaire
**POST** `{{BASE_URL}}/api/users/{{USER_ID}}/weekly-plan`

**Body (JSON) :**
```json
{
  "week_start_date": "2025-06-16",
  "meals": [
    {
      "day_of_week": 1,
      "meal_type": "petit-déjeuner",
      "food_id": 15,
      "planned_quantity": 1
    },
    {
      "day_of_week": 1,
      "meal_type": "déjeuner",
      "food_id": 2,
      "planned_quantity": 1
    },
    {
      "day_of_week": 2,
      "meal_type": "petit-déjeuner",
      "food_id": 15,
      "planned_quantity": 1
    }
  ]
}
```

**Réponse attendue :**
```json
{
  "success": true,
  "message": "Plan hebdomadaire créé avec succès"
}
```

### 7.2 Récupération du plan hebdomadaire
**GET** `{{BASE_URL}}/api/users/{{USER_ID}}/weekly-plan?week_start_date=2025-06-16`

**Réponse attendue :**
```json
{
  "user_id": 1,
  "week_start_date": "2025-06-16",
  "weekly_plan": [
    {
      "id": 1,
      "day_of_week": 1,
      "meal_type": "petit-déjeuner",
      "food_id": 15,
      "planned_quantity": 1,
      "food_name": "Salade de Marie",
      "category": "Entrée",
      "ingredients": "Laitue, tomates, concombre, avocat"
    },
    {
      "id": 2,
      "day_of_week": 1,
      "meal_type": "déjeuner",
      "food_id": 2,
      "planned_quantity": 1,
      "food_name": "Poulet DG",
      "category": "Plat principal",
      "ingredients": "Poulet, plantain, légumes"
    }
  ]
}
```

---

## 8. GESTION DES BUFFETS

### 8.1 Création d'un événement buffet
**POST** `{{BASE_URL}}/api/buffet-events`

**Body (JSON) :**
```json
{
  "event_name": "Anniversaire de Marie",
  "event_date": "2025-06-20",
  "estimated_guests": 25,
  "created_by": 1,
  "foods": [
    {
      "food_id": 1,
      "planned_quantity": 15,
      "unit": "portions"
    },
    {
      "food_id": 2,
      "planned_quantity": 20,
      "unit": "portions"
    },
    {
      "food_id": 15,
      "planned_quantity": 8,
      "unit": "portions"
    }
  ]
}
```

**Réponse attendue :**
```json
{
  "success": true,
  "buffet_id": 1,
  "message": "Événement buffet créé avec succès"
}
```
*Sauvegarder BUFFET_ID = 1*

### 8.2 Récupération des détails du buffet
**GET** `{{BASE_URL}}/api/buffet-events/{{BUFFET_ID}}`

**Réponse attendue :**
```json
{
  "id": 1,
  "event_name": "Anniversaire de Marie",
  "event_date": "2025-06-20",
  "estimated_guests": 25,
  "created_by": 1,
  "creator_username": "marie_dubois",
  "foods": [
    {
      "id": 1,
      "food_id": 1,
      "planned_quantity": 15,
      "unit": "portions",
      "food_name": "Ndolé",
      "category": "Plat principal",
      "ingredients": "Feuilles de ndolé, arachides, poisson, viande"
    },
    {
      "id": 2,
      "food_id": 2,
      "planned_quantity": 20,
      "unit": "portions",
      "food_name": "Poulet DG",
      "category": "Plat principal",
      "ingredients": "Poulet, plantain, légumes"
    }
  ]
}
```

### 8.3 Calcul des quantités recommandées
**GET** `{{BASE_URL}}/api/buffet-events/{{BUFFET_ID}}/calculate-quantities`

**Réponse attendue :**
```json
{
  "buffet_id": 1,
  "estimated_guests": 25,
  "recommendations": [
    {
      "food_id": 1,
      "food_name": "Ndolé",
      "category": "Plat principal",
      "planned_quantity": 15,
      "recommended_quantity": 30.0,
      "per_person": 1.2,
      "unit": "portions"
    },
    {
      "food_id": 2,
      "food_name": "Poulet DG",
      "category": "Plat principal",
      "planned_quantity": 20,
      "recommended_quantity": 30.0,
      "per_person": 1.2,
      "unit": "portions"
    }
  ]
}
```

### 8.4 Liste de tous les événements buffet
**GET** `{{BASE_URL}}/api/buffet-events`

**Réponse attendue :**
```json
{
  "buffet_events": [
    {
      "id": 1,
      "event_name": "Anniversaire de Marie",
      "event_date": "2025-06-20",
      "estimated_guests": 25,
      "created_by": 1,
      "creator_username": "marie_dubois"
    }
  ]
}
```

---

## 9. STATISTIQUES ET RECOMMANDATIONS

### 9.1 Tableau de bord utilisateur
**GET** `{{BASE_URL}}/api/users/{{USER_ID}}/dashboard?days=30`

**Réponse attendue :**
```json
{
  "user_id": 1,
  "period_days": 30,
  "statistics": {
    "total_meals": 2,
    "total_symptoms": 2,
    "avg_meals_per_day": 0.1,
    "avg_symptoms_per_day": 0.1
  },
  "allergy_analysis": {
    "total_potential_allergies": 1,
    "high_risk_foods": 0,
    "top_risks": [
      {
        "food_name": "Ndolé",
        "risk_score": 35.5
      }
    ]
  },
  "consumption_patterns": {
    "most_consumed_foods": [
      {
        "food": "Ndolé",
        "count": 1
      },
      {
        "food": "Salade de Marie",
        "count": 1
      }
    ]
  }
}
```

### 9.2 Recommandations personnalisées
**GET** `{{BASE_URL}}/api/users/{{USER_ID}}/recommendations`

**Réponse attendue :**
```json
{
  "user_id": 1,
  "recommendations": [
    {
      "type": "diversification",
      "priority": "medium",
      "title": "Diversifiez votre alimentation",
      "message": "Essayez d'inclure plus de variété dans vos repas pour une meilleure santé.",
      "suggestion": "Explorez de nouveaux aliments de notre base de données"
    },
    {
      "type": "symptom_pattern",
      "priority": "medium",
      "title": "Symptômes récurrents détectés",
      "message": "Vous avez rapporté 2 fois le symptôme \"Nausées\". Surveillez vos habitudes alimentaires.",
      "action": "Tenez un journal plus détaillé"
    }
  ],
  "total_recommendations": 2,
  "generated_at": "2025-06-12T17:00:00.000Z"
}
```

---

## 10. EXPORT ET GESTION DES DONNÉES

### 10.1 Export des données utilisateur
**GET** `{{BASE_URL}}/api/export/{{USER_ID}}/data`

**Réponse attendue :**
```json
{
  "user_info": {
    "id": 1,
    "username": "marie_dubois",
    "email": "marie.dubois.updated@email.com",
    "created_at": "2025-06-12T10:05:00.000Z"
  },
  "meals": [
    {
      "id": 1,
      "food_name": "Salade de Marie",
      "meal_time": "2025-06-12T08:00:00.000Z",
      "quantity": 1,
      "notes": "Petit-déjeuner léger avec avocat",
      "ingredients": "Laitue, tomates, concombre, avocat"
    }
  ],
  "symptoms": [
    {
      "id": 1,
      "symptom_type": "Ballonnements",
      "severity": 2,
      "occurrence_time": "2025-06-12T15:30:00.000Z",
      "description": "Légers ballonnements après le déjeuner"
    }
  ],
  "allergy_analysis": [
    {
      "food_name": "Ndolé",
      "risk_score": 35.5
    }
  ],
  "export_date": "2025-06-12T17:30:00.000Z"
}
```

### 10.2 Statistiques avant suppression
**GET** `{{BASE_URL}}/api/users/{{USER_ID}}/stats`

**Réponse attendue :**
```json
{
  "user_id": 1,
  "username": "marie_dubois",
  "data_summary": {
    "meals_recorded": 2,
    "symptoms_logged": 2,
    "weekly_plans": 3,
    "buffet_events_created": 1,
    "total_records": 8
  },
  "warning": "La suppression de cet utilisateur effacera définitivement toutes ces données"
}
```

---

## 11. GESTION DES IMAGES

### 11.1 Récupération des images d'un aliment
**GET** `{{BASE_URL}}/api/foods/{{FOOD_ID}}/images`

**Réponse attendue :**
```json
{
  "food_id": 15,
  "food_name": "Salade de Marie",
  "images": [
    {
      "id": 1,
      "file_path": "/media/images/salade_de_marie_1.jpg",
      "image_url": "/api/media/salade_de_marie_1.jpg",
      "original_url": "https://example.com/salade.jpg",
      "is_primary": true,
      "file_size": 45230,
      "created_at": "2025-06-12T10:15:00.000Z"
    },
    {
      "id": 2,
      "file_path": "/media/images/salade_de_marie_2.jpg",
      "image_url": "/api/media/salade_de_marie_2.jpg",
      "original_url": "https://example.com/salade2.jpg",
      "is_primary": false,
      "file_size": 38450,
      "created_at": "2025-06-12T10:20:00.000Z"
    }
  ],
  "total_images": 2
}
```

### 11.2 Définir une image comme principale
**PUT** `{{BASE_URL}}/api/images/2/primary`

**Réponse attendue :**
```json
{
  "success": true,
  "message": "Image définie comme principale"
}
```

### 11.3 Accès à un fichier image
**GET** `{{BASE_URL}}/api/media/salade_de_marie_1.jpg`

**Réponse attendue :** Fichier image binaire avec headers appropriés

---

## 12. TESTS DE VALIDATION ET D'ERREUR

### 12.1 Création d'utilisateur avec email existant
**POST** `{{BASE_URL}}/api/users`

**Body (JSON) :**
```json
{
  "username": "marie_test",
  "email": "marie.dubois.updated@email.com"
}
```

**Réponse attendue :**
```json
{
  "error": "Utilisateur déjà existant"
}
```
**Status Code :** 409

### 12.2 Recherche d'utilisateur inexistant
**GET** `{{BASE_URL}}/api/users/999`

**Réponse attendue :**
```json
{
  "error": "Utilisateur non trouvé"
}
```
**Status Code :** 404

### 12.3 Création de repas avec données manquantes
**POST** `{{BASE_URL}}/api/meals`

**Body (JSON) :**
```json
{
  "user_id": 1,
  "meal_time": "2025-06-12T08:00:00.000Z"
}
```

**Réponse attendue :**
```json
{
  "error": "Tous les champs requis doivent être fournis"
}
```
**Status Code :** 400

### 12.4 Symptôme avec sévérité invalide
**POST** `{{BASE_URL}}/api/symptoms`

**Body (JSON) :**
```json
{
  "user_id": 1,
  "symptom_type": "Test",
  "severity": 10,
  "occurrence_time": "2025-06-12T15:30:00.000Z"
}
```

**Réponse attendue :**
```json
{
  "error": "La sévérité doit être entre 1 et 5"
}
```
**Status Code :** 400

---

## 13. NETTOYAGE (OPTIONNEL)

### 13.1 Suppression de l'utilisateur (avec confirmation)
**DELETE** `{{BASE_URL}}/api/users/{{USER_ID}}?confirm=true`

**Réponse attendue :**
```json
{
  "success": true,
  "message": "Utilisateur marie_dubois supprimé avec succès",
  "deleted_user": {
    "id": 1,
    "username": "marie_dubois",
    "email": "marie.dubois.updated@email.com"
  }
}
```

---

## Résumé des Tests

**Total des requêtes :** 35+
**Modules testés :**
- ✅ Initialisation système
- ✅ Gestion utilisateurs (CRUD complet)
- ✅ Gestion aliments avec images
- ✅ Enregistrement repas
- ✅ Suivi symptômes
- ✅ Analyse allergies
- ✅ Planification hebdomadaire
- ✅ Gestion buffets
- ✅ Statistiques et recommandations
- ✅ Export de données
- ✅ Gestion des images
- ✅ Validation des erreurs

**Ordre d'exécution recommandé :** Suivre l'ordre numérique pour respecter les dépendances entre les tests.

**Variables à sauvegarder :** USER_ID, FOOD_ID, BUFFET_ID pour la continuité des tests.