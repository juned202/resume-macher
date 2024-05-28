from flask import Flask, request, jsonify, render_template, make_response
import fitz  # PyMuPDF
import docx
import spacy
from io import BytesIO
from collections import Counter
from spacy.lang.en.stop_words import STOP_WORDS

app = Flask(__name__)

# Load the spaCy model
nlp = spacy.load('en_core_web_sm')

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_docx(file):
    doc = docx.Document(BytesIO(file.read()))
    text = "\n".join([para.text for para in doc.paragraphs])
    return text



def extract_keywords(text):
    doc = nlp(text)
    
    # Get the frequency distribution of words
    word_freq = Counter(token.text.lower() for token in doc if token.is_alpha and len(token) > 2)
    
    # Get the most common words to exclude
    most_common_words = set(word for word, freq in word_freq.most_common(10))  # Adjust the number as needed
    
    # Remove stop words and most common words
    keywords = set(token.text for token in doc if token.text.lower() not in STOP_WORDS and token.text.lower() not in most_common_words)
    
    return keywords


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
  try:
    resume = request.files['resume']
    job_description = request.files['jobDescription']
    
    if resume.filename.endswith('.pdf'):
        resume_text = extract_text_from_pdf(resume)
    elif resume.filename.endswith('.docx'):
        resume_text = extract_text_from_docx(resume)
    
    if job_description.filename.endswith('.pdf'):
        job_description_text = extract_text_from_pdf(job_description)
    elif job_description.filename.endswith('.docx'):
        job_description_text = extract_text_from_docx(job_description)
    
    resume_keywords = extract_keywords(resume_text)
    job_description_keywords = extract_keywords(job_description_text)
    
    matched_keywords = resume_keywords & job_description_keywords
    missing_keywords = job_description_keywords - resume_keywords
    match_percentage = (len(matched_keywords) / len(job_description_keywords)) * 100
    
    return jsonify({
        'missing_keywords': list(missing_keywords),
        'match_percentage': match_percentage
    })

  except Exception as e:
         return make_response(jsonify({'error': str(e)}), 500)

if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0')
