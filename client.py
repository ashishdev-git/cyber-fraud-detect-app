import base64

import streamlit as st

from app.service import FraudRequest, FeedbackRequest, AnalysisUnavailable, analyze_fraud, feedback
st.set_page_config(page_title='CyberShield', page_icon='🛡️', layout='centered')
st.title('🛡️ CyberShield')
st.caption('Understand suspicious messages, screenshots, and links.')

SAMPLES = {
    'Lottery scam': 'Congratulations! You won Rs 25 lakh. Pay Rs 5000 processing fee to claim your prize.',
    'Bank phishing': 'Your bank account will be blocked today. Update KYC now at https://bank-verify.example/login',
    'Hindi scam': 'बधाई हो! आपने 25 लाख रुपये जीते हैं। इनाम पाने के लिए पहले 5000 रुपये भेजें।',
    'Hinglish scam': 'Main bank se bol raha hoon. Account band hone wala hai, abhi apna OTP batao.',
    'Normal message': 'Hi, our meeting is confirmed for 3 PM tomorrow. See you at the office.',
}


def load_sample(text):
    st.session_state.message = text
    st.session_state.upload_version = st.session_state.get('upload_version', 0) + 1
    st.session_state.pop('result', None)
    st.session_state.pop('feedback_saved', None)


st.write('Try a sample')
columns = st.columns(3)
for index, (label, text) in enumerate(SAMPLES.items()):
    columns[index % 3].button(label, on_click=load_sample, args=(text,), use_container_width=True)

message = st.text_area('Message or URL', key='message', height=150, max_chars=10000,
                       placeholder='Paste a suspicious message, or upload a screenshot below.')
language = st.selectbox('Response language', ['English', 'Hindi', 'Hinglish'])
uploaded = st.file_uploader('Screenshot (optional, maximum 5 MB)', type=['png', 'jpg', 'jpeg', 'webp'],
                            key='upload_' + str(st.session_state.get('upload_version', 0)),
                            help='Maximum 5 MB. PNG, JPEG, or WebP. Screenshots are sent to Gemini for analysis.')
st.caption('Remove passwords, OTPs, and account details before submitting. Messages and screenshots are sent to Gemini.')
image_bytes = uploaded.getvalue() if uploaded else None
if image_bytes and len(image_bytes) <= 5 * 1024 * 1024:
    try:
        st.image(image_bytes, caption='Screenshot to analyse', width=320)
    except Exception:
        st.warning('Cannot preview this image. Upload a valid PNG, JPEG, or WebP.')


if st.button('Analyse', type='primary', use_container_width=True):
    st.session_state.pop('result', None)
    st.session_state.pop('feedback_saved', None)
    if not message.strip() and not image_bytes:
        st.warning('Enter a message or upload a screenshot.')
    elif image_bytes and len(image_bytes) > 5 * 1024 * 1024:
        st.error('Screenshot must be 5 MB or smaller.')
    else:
        payload = {'message': message, 'language': language}
        if image_bytes:
            payload['image_base64'] = base64.b64encode(image_bytes).decode()
        try:
            with st.spinner('Reviewing your message and screenshot…'):
                st.session_state.result = analyze_fraud(FraudRequest(**payload))
            st.session_state.result_language = language
        except AnalysisUnavailable as error:
            st.error(str(error))
        except ValueError as error:
            st.error(str(error))

result = st.session_state.get('result')
if result:
    data = result['analysis']
    st.divider()
    st.caption('Latest assessment · ' + st.session_state.get('result_language', 'English'))
    badges = {
        'LOW': ('🟢 LOW RISK', st.success),
        'MEDIUM': ('🟠 MEDIUM RISK', st.warning),
        'HIGH': ('🔴 HIGH RISK', st.error),
        'CRITICAL': ('🚨 CRITICAL RISK', st.error),
    }
    label, display = badges[data['risk_level']]
    display(label)
    st.caption('AI assessment based on submitted evidence; LOW does not guarantee safety.')
    st.write('Fraud type')
    st.text(data['fraud_type'])
    st.write('Assessment')
    st.text(data['summary'])
    st.write('Suspicious indicators')
    if not data['indicators']:
        st.text('No concrete indicators identified.')
    for indicator in data['indicators']:
        st.text('• ' + indicator)
    st.write('Recommended next step')
    st.text(data['recommendation'])
    if data.get('needs_more_information'):
        st.write('More information needed')
        st.text(data.get('follow_up_question') or 'Please provide more context.')
    if data.get('extracted_text'):
        with st.expander('Text read from screenshot'):
            st.text(data['extracted_text'])

    if result.get('url_checks'):
        st.write('URL assessment')
        st.caption('Visible patterns only — links are not opened and live reputation is not checked. Up to 10 links shown.')
        for check in result['url_checks']:
            with st.container(border=True):
                st.text(check['url'])
                st.text(check['status'])
                for indicator in check['indicators']:
                    st.text('• ' + indicator)
                st.text(check['reputation'])

    st.write('Was this assessment useful?')
    left, right = st.columns(2)
    vote = None
    if left.button('👍 Helpful', use_container_width=True):
        vote = 'helpful'
    if right.button('👎 Not helpful', use_container_width=True):
        vote = 'not_helpful'
    if vote:
        try:
            feedback(FeedbackRequest(analysis_id=result['analysis_id'], rating=vote))
            st.session_state.feedback_saved = vote
        except (LookupError, ValueError, OSError):
            st.error('Feedback could not be saved. Please try again.')
    if st.session_state.get('feedback_saved'):
        st.success('Thanks — your feedback has been saved.')
    st.caption('Feedback stores only a random assessment ID, risk label, rating, and timestamp locally. Submitted text and images are not saved by this app.')
