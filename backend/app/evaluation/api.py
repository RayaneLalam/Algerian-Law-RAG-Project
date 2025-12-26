# app/evaluation/routes.py
from flask import Blueprint, request, jsonify, g
from database.db_setup import get_db
import json
from datetime import datetime
from app.auth.auth_middleware import admin_required

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/api/evaluation')

def get_current_user_id():
    """Helper to get current user ID from Flask's g object (set by auth middleware)"""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user['id']
    # Fallback for development/testing
    return None

@evaluation_bp.route('/create', methods=['POST'])
@admin_required
def create_evaluation():
    """Create a new evaluation with candidate responses"""
    data = request.get_json()
    prompt = data.get('prompt')
    num_responses = data.get('num_responses', 1)
    model_version_id = data.get('model_version_id')
    dataset_example_id = data.get('dataset_example_id')
    golden_label = data.get('golden_label')
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    db = get_db()
    evaluator_id = get_current_user_id()
    
    if not evaluator_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    try:
        # Create evaluation record
        cursor = db.execute(
            '''INSERT INTO evaluations 
            (evaluator_id, model_version_id, prompt, dataset_example_id, num_responses, golden_label, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (evaluator_id, model_version_id, prompt, dataset_example_id, num_responses, golden_label, 'pending')
        )
        evaluation_id = cursor.lastrowid
        
        # Generate candidate responses (mock for now - integrate with your RAG system)
        candidates = []
        for i in range(num_responses):
            response_text = f"Mock response {i+1} for: {prompt}"
            cursor = db.execute(
                '''INSERT INTO evaluation_candidate 
                (evaluation_id, model_version_id, response_text, tokens)
                VALUES (?, ?, ?, ?)''',
                (evaluation_id, model_version_id, response_text, len(response_text.split()))
            )
            candidate_id = cursor.lastrowid
            candidates.append({
                'id': candidate_id,
                'response_text': response_text,
                'tokens': len(response_text.split())
            })
        
        # Update evaluation status
        db.execute(
            'UPDATE evaluations SET status = ? WHERE id = ?',
            ('running', evaluation_id)
        )
        
        db.commit()
        
        # Fetch created evaluation
        evaluation = db.execute(
            'SELECT * FROM evaluations WHERE id = ?',
            (evaluation_id,)
        ).fetchone()
        
        return jsonify({
            'evaluation': dict(evaluation),
            'candidates': candidates
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/rank', methods=['POST'])
@admin_required
def rank_candidate():
    """Rank an evaluation candidate"""
    data = request.get_json()
    candidate_id = data.get('candidate_id')
    rank = data.get('rank')
    comment = data.get('comment', '')
    
    if not candidate_id or not rank:
        return jsonify({'error': 'Candidate ID and rank are required'}), 400
    
    db = get_db()
    
    try:
        db.execute(
            '''UPDATE evaluation_candidate 
            SET rank_by_evaluator = ?, evaluator_comment = ?
            WHERE id = ?''',
            (rank, comment, candidate_id)
        )
        db.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/complete', methods=['POST'])
@admin_required
def complete_evaluation():
    """Mark an evaluation as completed"""
    data = request.get_json()
    evaluation_id = data.get('evaluation_id')
    
    if not evaluation_id:
        return jsonify({'error': 'Evaluation ID is required'}), 400
    
    db = get_db()
    
    try:
        db.execute(
            '''UPDATE evaluations 
            SET status = ?, completed_at = ?
            WHERE id = ?''',
            ('completed', datetime.now(), evaluation_id)
        )
        db.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/history', methods=['GET'])
@admin_required
def get_evaluation_history():
    """Get evaluation history for current user"""
    db = get_db()
    evaluator_id = get_current_user_id()
    
    if not evaluator_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    try:
        evaluations = db.execute(
            '''SELECT e.*, COUNT(ec.id) as candidate_count
            FROM evaluations e
            LEFT JOIN evaluation_candidate ec ON e.id = ec.evaluation_id
            WHERE e.evaluator_id = ?
            GROUP BY e.id
            ORDER BY e.created_at DESC
            LIMIT 50''',
            (evaluator_id,)
        ).fetchall()
        
        return jsonify({
            'evaluations': [dict(row) for row in evaluations]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/anonymous-queries', methods=['GET'])
@admin_required
def get_anonymous_queries():
    """Get anonymous user queries for hallucination review"""
    db = get_db()
    
    try:
        # Get messages from conversations without evaluations
        # or where sender_user_id is null (anonymous)
        queries = db.execute(
            '''SELECT 
                m.id,
                m.content,
                m.created_at,
                m.conversation_id,
                m.metadata,
                response.content as response
            FROM messages m
            LEFT JOIN messages response ON response.conversation_id = m.conversation_id 
                AND response.id > m.id 
                AND response.role = 'assistant'
            ORDER BY m.created_at DESC
            LIMIT 50''',
        ).fetchall()
        
        result = []
        for row in queries:
            query_dict = dict(row)
            # Parse metadata if it exists
            if query_dict.get('metadata'):
                try:
                    query_dict['metadata'] = json.loads(query_dict['metadata'])
                except:
                    pass
            result.append(query_dict)
        
        return jsonify({
            'queries': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/mark-hallucination', methods=['POST'])
@admin_required
def mark_hallucination():
    """Mark a message response as hallucination or accurate"""
    data = request.get_json()
    message_id = data.get('message_id')
    is_hallucination = data.get('is_hallucination', False)
    notes = data.get('notes', '')
    
    if not message_id:
        return jsonify({'error': 'Message ID is required'}), 400
    
    db = get_db()
    reviewer_id = get_current_user_id()
    
    if not reviewer_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    try:
        # Update message metadata with hallucination flag
        message = db.execute(
            'SELECT metadata FROM messages WHERE id = ?',
            (message_id,)
        ).fetchone()
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        metadata = json.loads(message['metadata']) if message['metadata'] else {}
        metadata['hallucination_review'] = {
            'is_hallucination': is_hallucination,
            'notes': notes,
            'reviewed_by': reviewer_id,
            'reviewed_at': datetime.now().isoformat()
        }
        
        db.execute(
            'UPDATE messages SET metadata = ? WHERE id = ?',
            (json.dumps(metadata), message_id)
        )
        db.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/metrics', methods=['GET'])
@admin_required
def get_metrics():
    """Get performance metrics for a model version on a dataset"""
    model_version_id = request.args.get('model_version_id', type=int)
    dataset_id = request.args.get('dataset_id', type=int)
    
    if not model_version_id:
        return jsonify({'error': 'Model version ID is required'}), 400
    
    db = get_db()
    
    try:
        query = '''
            SELECT 
                mm.id,
                mm.score,
                mm.computed_at,
                mt.name,
                mt.description,
                mm.metadata
            FROM model_metrics mm
            JOIN metric_types mt ON mm.metric_type_id = mt.id
            WHERE mm.model_version_id = ?
        '''
        params = [model_version_id]
        
        if dataset_id:
            query += ' AND (mm.dataset_id = ? OR mm.dataset_id IS NULL)'
            params.append(dataset_id)
        
        query += ' ORDER BY mt.name'
        
        metrics = db.execute(query, params).fetchall()
        
        return jsonify({
            'metrics': [dict(row) for row in metrics]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/models', methods=['GET'])
@admin_required
def get_models():
    """Get list of available model versions"""
    db = get_db()
    
    try:
        models = db.execute(
            '''SELECT 
                mv.id,
                mv.version,
                mv.description,
                mv.is_default,
                bm.name,
                bm.provider
            FROM model_versions mv
            JOIN base_models bm ON mv.base_model_id = bm.id
            ORDER BY mv.is_default DESC, mv.created_at DESC'''
        ).fetchall()
        
        return jsonify({
            'models': [dict(row) for row in models]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/datasets', methods=['GET'])
@admin_required
def get_datasets():
    """Get list of available datasets"""
    db = get_db()
    
    try:
        datasets = db.execute(
            '''SELECT 
                id,
                title,
                description,
                source_type,
                visibility,
                created_at
            FROM datasets
            ORDER BY created_at DESC'''
        ).fetchall()
        
        return jsonify({
            'datasets': [dict(row) for row in datasets]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/evaluation/<int:eval_id>', methods=['GET'])
@admin_required
def get_evaluation_detail(eval_id):
    """Get detailed information about a specific evaluation"""
    db = get_db()
    evaluator_id = get_current_user_id()
    
    if not evaluator_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    try:
        evaluation = db.execute(
            'SELECT * FROM evaluations WHERE id = ? AND evaluator_id = ?',
            (eval_id, evaluator_id)
        ).fetchone()
        
        if not evaluation:
            return jsonify({'error': 'Evaluation not found or access denied'}), 404
        
        candidates = db.execute(
            '''SELECT * FROM evaluation_candidate 
            WHERE evaluation_id = ?
            ORDER BY rank_by_evaluator ASC, created_at ASC''',
            (eval_id,)
        ).fetchall()
        
        return jsonify({
            'evaluation': dict(evaluation),
            'candidates': [dict(row) for row in candidates]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/discard/<int:eval_id>', methods=['POST'])
@admin_required
def discard_evaluation(eval_id):
    """Discard an evaluation"""
    db = get_db()
    evaluator_id = get_current_user_id()
    
    if not evaluator_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    try:
        # Check if evaluation belongs to current user
        evaluation = db.execute(
            'SELECT id FROM evaluations WHERE id = ? AND evaluator_id = ?',
            (eval_id, evaluator_id)
        ).fetchone()
        
        if not evaluation:
            return jsonify({'error': 'Evaluation not found or access denied'}), 404
        
        db.execute(
            'UPDATE evaluations SET status = ? WHERE id = ?',
            ('discarded', eval_id)
        )
        db.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


# Additional helper routes for RLHF workflow

@evaluation_bp.route('/batch-evaluate', methods=['POST'])
@admin_required
def batch_evaluate():
    """Create multiple evaluations from a dataset"""
    data = request.get_json()
    dataset_id = data.get('dataset_id')
    model_version_id = data.get('model_version_id')
    num_responses = data.get('num_responses', 3)
    limit = data.get('limit', 10)
    
    if not dataset_id or not model_version_id:
        return jsonify({'error': 'Dataset ID and Model Version ID are required'}), 400
    
    db = get_db()
    evaluator_id = get_current_user_id()
    
    if not evaluator_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    try:
        # Get examples from dataset
        examples = db.execute(
            '''SELECT * FROM dataset_training_example 
            WHERE dataset_id = ? 
            ORDER BY RANDOM() 
            LIMIT ?''',
            (dataset_id, limit)
        ).fetchall()
        
        created_evaluations = []
        
        for example in examples:
            # Create evaluation
            cursor = db.execute(
                '''INSERT INTO evaluations 
                (evaluator_id, model_version_id, prompt, dataset_example_id, 
                num_responses, golden_label, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (evaluator_id, model_version_id, example['prompt'], 
                example['id'], num_responses, example['gold_label'], 'pending')
            )
            eval_id = cursor.lastrowid
            created_evaluations.append(eval_id)
            
            # Generate candidates
            for i in range(num_responses):
                response_text = f"Generated response {i+1} for: {example['prompt']}"
                db.execute(
                    '''INSERT INTO evaluation_candidate 
                    (evaluation_id, model_version_id, response_text, tokens)
                    VALUES (?, ?, ?, ?)''',
                    (eval_id, model_version_id, response_text, len(response_text.split()))
                )
        
        db.commit()
        
        return jsonify({
            'success': True,
            'evaluations_created': len(created_evaluations),
            'evaluation_ids': created_evaluations
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/compute-metrics', methods=['POST'])
@admin_required
def compute_metrics():
    """Compute metrics for a model version on a dataset"""
    data = request.get_json()
    model_version_id = data.get('model_version_id')
    dataset_id = data.get('dataset_id')
    
    if not model_version_id:
        return jsonify({'error': 'Model version ID is required'}), 400
    
    db = get_db()
    
    try:
        # Get all completed evaluations for this model/dataset
        query = '''
            SELECT e.*, ec.rank_by_evaluator
            FROM evaluations e
            JOIN evaluation_candidate ec ON e.id = ec.evaluation_id
            WHERE e.model_version_id = ?
                AND e.status = 'completed'
                AND ec.rank_by_evaluator IS NOT NULL
        '''
        params = [model_version_id]
        
        if dataset_id:
            query += ' AND e.dataset_example_id IN (SELECT id FROM dataset_training_example WHERE dataset_id = ?)'
            params.append(dataset_id)
        
        evaluations = db.execute(query, params).fetchall()
        
        if not evaluations:
            return jsonify({'error': 'No completed evaluations found'}), 404
        
        # Calculate metrics
        ranks = [row['rank_by_evaluator'] for row in evaluations]
        avg_rank = sum(ranks) / len(ranks)
        
        # Get or create metric type
        metric = db.execute(
            "SELECT id FROM metric_types WHERE name = 'average_rank'"
        ).fetchone()
        
        if not metric:
            cursor = db.execute(
                "INSERT INTO metric_types (name, description) VALUES (?, ?)",
                ('average_rank', 'Average rank from RLHF evaluations')
            )
            metric_type_id = cursor.lastrowid
        else:
            metric_type_id = metric['id']
        
        # Insert or update metric
        db.execute(
            '''INSERT OR REPLACE INTO model_metrics 
            (model_version_id, dataset_id, metric_type_id, score, computed_at)
            VALUES (?, ?, ?, ?, ?)''',
            (model_version_id, dataset_id, metric_type_id, avg_rank, datetime.now())
        )
        
        db.commit()
        
        return jsonify({
            'success': True,
            'metric': {
                'name': 'average_rank',
                'score': avg_rank,
                'evaluations_count': len(evaluations)
            }
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500