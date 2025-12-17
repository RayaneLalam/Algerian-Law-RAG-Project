"""
Flask blueprint implementing the evaluation REST API.

This version integrates with the existing db_setup.py infrastructure.
"""
import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, abort, current_app
from database.db_setup import get_db

evaluation_bp = Blueprint('evaluation', __name__)


# ---------- Utility helpers -------------------------------------------------

def make_uuid():
    return str(uuid.uuid4())


# ---------- Stubbed model generator ----------------------------------------

def generate_model_responses(model_version_id: str, prompt: str, n: int):
    """Replace this stub with your real LLM call.
    Returns a list of dicts with keys: text (str) and optional meta (dict).
    """
    base_variants = [
        "Short answer: {}",
        "Detailed answer: {} Here's more context...",
        "Concise summary: {}",
        "Example-based answer: {} Example: ...",
    ]
    outs = []
    for i in range(n):
        template = base_variants[i % len(base_variants)]
        text = template.format(prompt[:120])
        outs.append({"text": text, "meta": {"mock_variant": i}})
    return outs


# ------------------ Evaluations endpoints ---------------------------------

@evaluation_bp.route('/evaluations', methods=['POST'])
def create_evaluation():
    req = request.get_json() or {}
    evaluator_id = req.get('evaluator_id')
    model_version_id = req.get('model_version_id')
    prompt = req.get('prompt')
    num_responses = int(req.get('num_responses', 1))
    dataset_example_id = req.get('dataset_example_id')

    if not model_version_id or not prompt:
        return jsonify({'error': 'model_version_id and prompt required'}), 400

    eval_id = make_uuid()
    
    db = get_db()
    db.execute("""
        INSERT INTO evaluations (id, evaluator_id, model_version_id, prompt, dataset_example_id, num_responses, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
    """, (eval_id, evaluator_id, model_version_id, prompt, dataset_example_id, num_responses))
    db.commit()
    
    return jsonify({'evaluation_id': eval_id}), 201


@evaluation_bp.route('/evaluations/<evaluation_id>/generate', methods=['POST'])
def generate_candidates(evaluation_id):
    db = get_db()
    
    eval_row = db.execute('SELECT * FROM evaluations WHERE id=?', (evaluation_id,)).fetchone()
    if not eval_row:
        abort(404, 'evaluation not found')
    
    if eval_row['status'] == 'completed':
        return jsonify({'error': 'evaluation already completed'}), 400

    num = int(request.json.get('num_responses', eval_row['num_responses']))
    model_version_id = eval_row['model_version_id']
    prompt = eval_row['prompt']

    candidates = generate_model_responses(model_version_id, prompt, num)

    candidate_ids = []
    for c in candidates:
        cid = make_uuid()
        candidate_ids.append(cid)
        db.execute("""
            INSERT INTO evaluation_candidate (id, evaluation_id, model_version_id, response_text, response_json, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (cid, evaluation_id, model_version_id, c['text'], json.dumps(c.get('meta', {}))))

    # set evaluation status to running
    db.execute("UPDATE evaluations SET status='running' WHERE id=?", (evaluation_id,))
    db.commit()

    return jsonify({'evaluation_id': evaluation_id, 'candidate_ids': candidate_ids, 'num_candidates': len(candidate_ids)}), 201


@evaluation_bp.route('/evaluations/<evaluation_id>', methods=['GET'])
def get_evaluation(evaluation_id):
    db = get_db()
    
    eval_row = db.execute('SELECT * FROM evaluations WHERE id=?', (evaluation_id,)).fetchone()
    if not eval_row:
        abort(404, 'evaluation not found')
    
    candidates = db.execute(
        'SELECT * FROM evaluation_candidate WHERE evaluation_id=? ORDER BY created_at',
        (evaluation_id,)
    ).fetchall()
    
    # Convert Row objects to dicts
    eval_dict = dict(eval_row)
    candidates_list = [dict(c) for c in candidates]
    
    return jsonify({'evaluation': eval_dict, 'candidates': candidates_list})


@evaluation_bp.route('/evaluations/<evaluation_id>/rank', methods=['POST'])
def submit_ranks(evaluation_id):
    payload = request.get_json() or {}
    ranks = payload.get('ranks', [])
    finalize = bool(payload.get('finalize', True))

    if not ranks:
        return jsonify({'error': 'ranks list required'}), 400

    db = get_db()
    
    for r in ranks:
        cid = r.get('candidate_id')
        rank = r.get('rank')
        comment = r.get('comment')
        if cid is None or rank is None:
            continue
        
        meta_fragment = json.dumps({'ranked_at': datetime.utcnow().isoformat()})
        db.execute("""
            UPDATE evaluation_candidate
            SET rank_by_evaluator = ?, evaluator_comment = ?, metadata = ?
            WHERE id = ?
        """, (rank, comment, meta_fragment, cid))

    if finalize:
        db.execute(
            'UPDATE evaluations SET status="completed", completed_at=CURRENT_TIMESTAMP WHERE id=?',
            (evaluation_id,)
        )

    # propagate RLHF to dataset_training_example if present
    eval_row = db.execute(
        'SELECT dataset_example_id, evaluator_id FROM evaluations WHERE id=?',
        (evaluation_id,)
    ).fetchone()
    
    if eval_row:
        ds_example_id = eval_row['dataset_example_id']
        evaluator_id = eval_row['evaluator_id']
        
        if ds_example_id:
            cands = db.execute("""
                SELECT id AS candidate_id, model_version_id, response_text, rank_by_evaluator 
                FROM evaluation_candidate 
                WHERE evaluation_id=? 
                ORDER BY rank_by_evaluator, created_at
            """, (evaluation_id,)).fetchall()
            
            rl_records = []
            for c in cands:
                rl_records.append({
                    'candidate_id': c['candidate_id'],
                    'model_version_id': c['model_version_id'],
                    'response_text': c['response_text'],
                    'rank': c['rank_by_evaluator'],
                    'evaluator_id': evaluator_id,
                    'from_evaluation_id': evaluation_id,
                    'ts': datetime.utcnow().isoformat()
                })
            
            # Update dataset_training_example with RLHF data
            db.execute("""
                UPDATE dataset_training_example 
                SET rlhf_ranked_labels = ?, 
                    metadata = ? 
                WHERE id = ?
            """, (
                json.dumps(rl_records),
                json.dumps({'last_rlhf_update': datetime.utcnow().isoformat()}),
                ds_example_id
            ))
    
    db.commit()
    return jsonify({'status': 'ok', 'updated': len(ranks)}), 200


# ---------------- Metrics endpoints ---------------------------------------

@evaluation_bp.route('/metrics', methods=['GET'])
def get_metrics():
    model_version_id = request.args.get('model_version_id')
    dataset_id = request.args.get('dataset_id')
    metric_name = request.args.get('metric_name')

    sql = """
    SELECT mm.id, mm.model_version_id, mm.dataset_id, mm.metric_type_id, mm.score, mm.metadata, mm.computed_at,
           mt.name AS metric_name, ds.title AS dataset_title, mv.version AS model_version
    FROM model_metrics mm
    LEFT JOIN metric_types mt ON mm.metric_type_id = mt.id
    LEFT JOIN datasets ds ON mm.dataset_id = ds.id
    LEFT JOIN model_versions mv ON mm.model_version_id = mv.id
    WHERE 1=1
    """
    params = []
    if model_version_id:
        sql += ' AND mm.model_version_id = ?'
        params.append(model_version_id)
    if dataset_id:
        sql += ' AND mm.dataset_id = ?'
        params.append(dataset_id)
    if metric_name:
        sql += ' AND mt.name = ?'
        params.append(metric_name)
    sql += ' ORDER BY mm.computed_at DESC'

    db = get_db()
    rows = db.execute(sql, params).fetchall()
    
    return jsonify({'metrics': [dict(r) for r in rows]})


@evaluation_bp.route('/metrics/best', methods=['GET'])
def get_best_models():
    dataset_id = request.args.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'dataset_id required'}), 400
    metric_name = request.args.get('metric_name', 'accuracy')

    sql = """
    SELECT mv.id AS model_version_id, mv.version, mt.name AS metric_name, mm.score
    FROM model_metrics mm
    JOIN metric_types mt ON mm.metric_type_id = mt.id
    JOIN model_versions mv ON mm.model_version_id = mv.id
    WHERE mm.dataset_id = ? AND mt.name = ?
    ORDER BY mm.score DESC
    LIMIT 10
    """
    
    db = get_db()
    rows = db.execute(sql, (dataset_id, metric_name)).fetchall()
    
    return jsonify({'best': [dict(r) for r in rows]})


@evaluation_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'uptime': True})