import json
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

import app as app_module
from train import fit_reference

CONFIG = json.loads(Path('config.json').read_text())
DF = pd.read_csv('dataset/train.csv')
client = TestClient(app_module.app)


def test_dataset_valid():
    assert len(DF) >= 100
    assert set(CONFIG['features'] + ['label']).issubset(DF.columns)
    assert DF['label'].nunique() == 2


def test_model_accuracy_sane():
    _, accuracy = fit_reference(DF, CONFIG)
    assert accuracy >= 0.5


def test_metrics_endpoint():
    r = client.get('/metrics')
    assert r.status_code == 200
    m = r.json()
    for key in ['student_id', 'accuracy', 'training_rows', 'model_version', 'git_sha']:
        assert key in m
    assert m['student_id'] == CONFIG['student_id']
    assert m['training_rows'] == len(DF)


def test_predict_endpoint():
    record = {f: 0.0 for f in CONFIG['features']}
    r = client.post('/predict', json={'records': [record]})
    assert r.status_code == 200
    assert len(r.json()['predictions']) == 1
