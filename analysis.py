from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Analysis, Patient, User
from datetime import datetime
import os
from werkzeug.utils import secure_filename

analysis_bp = Blueprint('analysis', __name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'avi'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@analysis_bp.route('/analyze/<int:patient_id>', methods=['POST'])
@jwt_required()
def analyze_emotion(patient_id):
    current_user_id = get_jwt_identity()
    patient = Patient.query.get_or_404(patient_id)
    
    if patient.clinician_id != current_user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400
        
    try:
        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Here you would normally call your emotion analysis model
        # This is a placeholder for the emotion analysis result
        analysis_result = {
            "dominant_emotion": "happy",
            "emotions": {
                "happy": 0.8,
                "sad": 0.1,
                "neutral": 0.1
            },
            "confidence": 0.9
        }
        
        # Create analysis record
        analysis = Analysis(
            patient_id=patient_id,
            clinician_id=current_user_id,
            analysis_type='image' if file.filename.lower().endswith(('png', 'jpg', 'jpeg')) else 'video',
            media_path=file_path,
            emotions_detected=analysis_result,
            confidence_score=analysis_result['confidence'],
            status='completed'
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        return jsonify({
            "message": "Analysis completed successfully",
            "analysis_id": analysis.id,
            "results": analysis_result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analysis_bp.route('/analyses/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_patient_analyses(patient_id):
    current_user_id = get_jwt_identity()
    patient = Patient.query.get_or_404(patient_id)
    
    if patient.clinician_id != current_user_id:
        return jsonify({"error": "Unauthorized"}), 403
        
    analyses = Analysis.query.filter_by(patient_id=patient_id).order_by(Analysis.analysis_date.desc()).all()
    
    return jsonify([{
        'id': a.id,
        'date': a.analysis_date.isoformat(),
        'type': a.analysis_type,
        'emotions_detected': a.emotions_detected,
        'confidence_score': a.confidence_score,
        'status': a.status,
        'notes': a.notes
    } for a in analyses])

@analysis_bp.route('/analysis/<int:analysis_id>', methods=['GET'])
@jwt_required()
def get_analysis(analysis_id):
    current_user_id = get_jwt_identity()
    analysis = Analysis.query.get_or_404(analysis_id)
    
    if analysis.clinician_id != current_user_id:
        return jsonify({"error": "Unauthorized"}), 403
        
    return jsonify({
        'id': analysis.id,
        'patient_id': analysis.patient_id,
        'date': analysis.analysis_date.isoformat(),
        'type': analysis.analysis_type,
        'emotions_detected': analysis.emotions_detected,
        'confidence_score': analysis.confidence_score,
        'status': analysis.status,
        'notes': analysis.notes
    })

@analysis_bp.route('/analysis/<int:analysis_id>/notes', methods=['PUT'])
@jwt_required()
def update_analysis_notes(analysis_id):
    current_user_id = get_jwt_identity()
    analysis = Analysis.query.get_or_404(analysis_id)
    
    if analysis.clinician_id != current_user_id:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json()
    analysis.notes = data.get('notes', '')
    db.session.commit()
    
    return jsonify({"message": "Notes updated successfully"})