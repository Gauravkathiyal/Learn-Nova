"""
API v1 Authentication Routes
"""

from flask import request, jsonify  # type: ignore[import]
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity  # type: ignore[import]
from models.user import User  # type: ignore[import]
from extensions import db  # type: ignore[import]
from api.v1 import v1  # type: ignore[import]

@v1.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    
    # Validate required fields
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    # Construct name from first_name and last_name
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    name = data.get('name', f'{first_name} {last_name}'.strip())
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    user = User(
        email=email,
        name=name
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict(),
        'access_token': access_token
    }), 201


@v1.route('/auth/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token
    }), 200


@v1.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@v1.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client should discard token)"""
    return jsonify({'message': 'Logout successful'}), 200
