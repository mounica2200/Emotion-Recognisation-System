from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Patient, User
from datetime import datetime

patients_bp = Blueprint('patients', __name__)

@patients_bp.route('/patients', methods=['POST'])
@jwt_required()
def create_patient():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'clinician':
        return jsonify({"error": "Only clinicians can add patients"}), 403
        
    try:
        data = request.get_json()
        new_patient = Patient(
            first_name=data['first_name'],
            last_name=data['last_name'],
            date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date(),
            gender=data.get('gender'),
            email=data.get('email'),
            phone=data.get('phone'),
            clinician_id=current_user_id
        )
        
        db.session.add(new_patient)
        db.session.commit()
        
        return jsonify({
            "message": "Patient added successfully",
            "patient_id": new_patient.id
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@patients_bp.route('/patients', methods=['GET'])
@jwt_required()
def get_patients():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'clinician':
        return jsonify({"error": "Unauthorized"}), 403
        
    patients = Patient.query.filter_by(clinician_id=current_user_id).all()
    
    return jsonify([{
        'id': p.id,
        'first_name': p.first_name,
        'last_name': p.last_name,
        'date_of_birth': p.date_of_birth.isoformat(),
        'gender': p.gender,
        'email': p.email,
        'phone': p.phone,
        'created_at': p.created_at.isoformat()
    } for p in patients])

@patients_bp.route('/patients/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_patient(patient_id):
    current_user_id = get_jwt_identity()
    patient = Patient.query.get_or_404(patient_id)
    
    if patient.clinician_id != current_user_id:
        return jsonify({"error": "Unauthorized"}), 403
        
    return jsonify({
        'id': patient.id,
        'first_name': patient.first_name,
        'last_name': patient.last_name,
        'date_of_birth': patient.date_of_birth.isoformat(),
        'gender': patient.gender,
        'email': patient.email,
        'phone': patient.phone,
        'created_at': patient.created_at.isoformat(),
        'analyses': [{
            'id': a.id,
            'date': a.analysis_date.isoformat(),
            'type': a.analysis_type,
            'status': a.status
        } for a in patient.analyses]
    })

@patients_bp.route('/patients/<int:patient_id>', methods=['PUT'])
@jwt_required()
def update_patient(patient_id):
    current_user_id = get_jwt_identity()
    patient = Patient.query.get_or_404(patient_id)
    
    if patient.clinician_id != current_user_id:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json()
    
    if 'first_name' in data:
        patient.first_name = data['first_name']
    if 'last_name' in data:
        patient.last_name = data['last_name']
    if 'date_of_birth' in data:
        patient.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
    if 'gender' in data:
        patient.gender = data['gender']
    if 'email' in data:
        patient.email = data['email']
    if 'phone' in data:
        patient.phone = data['phone']
        
    db.session.commit()
    
    return jsonify({"message": "Patient updated successfully"})

@patients_bp.route('/patients/<int:patient_id>', methods=['DELETE'])
@jwt_required()
def delete_patient(patient_id):
    current_user_id = get_jwt_identity()
    patient = Patient.query.get_or_404(patient_id)
    
    if patient.clinician_id != current_user_id:
        return jsonify({"error": "Unauthorized"}), 403
        
    db.session.delete(patient)
    db.session.commit()
    
    return jsonify({"message": "Patient deleted successfully"})