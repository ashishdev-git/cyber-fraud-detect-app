import base64
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from PIL import Image
from streamlit.testing.v1 import AppTest

from app.main import app
from app.images import prepare_image
from app.schemas import FraudAnalysis
from app.urls import check_urls

ASSESSMENT = dict(risk_level='HIGH', fraud_probability=0.9, fraud_type='Scam',
                  summary='Suspicious payment request.', indicators=['Upfront fee'],
                  recommendation='Do not pay.', needs_more_information=False,
                  follow_up_question=None, extracted_text='')


def screenshot():
    out = io.BytesIO()
    Image.new('RGB', (100, 50), 'white').save(out, 'PNG')
    return base64.b64encode(out.getvalue()).decode()


class Features(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'CYBERSHIELD_DB': str(Path(self.tmp.name) / 'test.sqlite3')})
        self.env.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_text_language_and_separate_messages(self):
        with patch('app.agent.model') as model:
            model.return_value.invoke.return_value = FraudAnalysis(**ASSESSMENT)
            response = self.client.post('/analyze', json={'message': 'OTP batao', 'language': 'Hinglish'})
            self.assertEqual(response.status_code, 200)
            messages = model.return_value.invoke.call_args.args[0]
            self.assertEqual(messages[0].type, 'system')
            self.assertIn('Selected response language: Hinglish', messages[0].content)
            self.assertEqual(messages[1].type, 'human')

    def test_screenshot_only_and_extracted_urls(self):
        data = dict(ASSESSMENT, extracted_text='Visit http://192.0.2.1/account')
        with patch('app.agent.model') as model:
            model.return_value.invoke.return_value = FraudAnalysis(**data)
            response = self.client.post('/analyze', json={'image_base64': screenshot(), 'language': 'Hindi'})
            self.assertEqual(response.status_code, 200)
            content = model.return_value.invoke.call_args.args[0][1].content
            self.assertTrue(content[1]['image_url']['url'].startswith('data:image/jpeg;base64,'))
            self.assertEqual(len(response.json()['url_checks']), 1)

    def test_invalid_input(self):
        for payload in ({}, {'message': ' '}, {'message': 'x', 'language': 'Other'},
                        {'image_base64': 'not an image'}, {'message': 'x' * 10001}):
            self.assertEqual(self.client.post('/analyze', json=payload).status_code, 422)

    def test_model_failure(self):
        with patch('app.main.fraud_agent.invoke', side_effect=RuntimeError('secret details')):
            response = self.client.post('/analyze', json={'message': 'test'})
            self.assertEqual(response.status_code, 502)
            self.assertNotIn('secret details', response.text)

    def test_feedback_updates_and_unknown_id(self):
        with patch('app.main.fraud_agent.invoke', return_value={'analysis': ASSESSMENT}):
            result = self.client.post('/analyze', json={'message': 'test'}).json()
        for rating in ['helpful', 'not_helpful']:
            self.assertEqual(self.client.post('/feedback', json={'analysis_id': result['analysis_id'], 'rating': rating}).status_code, 200)
        self.assertEqual(self.client.post('/feedback', json={'analysis_id': str(uuid4()), 'rating': 'helpful'}).status_code, 404)
        self.assertEqual(self.client.post('/feedback', json={'analysis_id': result['analysis_id'], 'rating': 'other'}).status_code, 422)

    def test_url_checks_do_not_request_links(self):
        with patch('requests.get') as get, patch('requests.post') as post:
            checks = check_urls('http://192.0.2.1/test https://bank.example@evil.example/path https://bit.ly/demo')
            self.assertEqual(len(checks), 3)
            self.assertTrue(all(c['indicators'] for c in checks))
            get.assert_not_called()
            post.assert_not_called()
        self.assertEqual(len(check_urls(' '.join('https://example.com/' + str(i) for i in range(20)))), 10)

    def test_valid_image(self):
        self.assertTrue(prepare_image(screenshot()).startswith('data:image/jpeg;base64,'))
        with self.assertRaises(ValueError):
            prepare_image(base64.b64encode(b'x' * (5 * 1024 * 1024 + 1)).decode())

    def test_ui_samples_results_and_feedback_survive_rerun(self):
        ui = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'client.py')).run()
        self.assertFalse(ui.exception)
        next(b for b in ui.button if b.label == 'Hindi scam').click().run()
        self.assertIn('बधाई', ui.text_area[0].value)
        with patch('requests.post') as post:
            post.return_value.ok = True
            post.return_value.json.return_value = {'analysis_id': str(uuid4()), 'analysis': ASSESSMENT, 'url_checks': []}
            next(b for b in ui.button if b.label == 'Analyse').click().run()
            self.assertFalse(ui.exception)
            self.assertIn('result', ui.session_state)
            post.return_value.json.return_value = {'success': True}
            next(b for b in ui.button if b.label == '👍 Helpful').click().run()
            self.assertFalse(ui.exception)
            self.assertEqual(ui.session_state['feedback_saved'], 'helpful')
            self.assertIn('result', ui.session_state)


if __name__ == '__main__':
    unittest.main()
