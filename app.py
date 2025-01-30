from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from forms import FeedbackForm
from datetime import datetime
import json
import csv
import io
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    course_ratings = db.Column(db.String(100), nullable=False)
    faculty_ratings = db.Column(db.String(100), nullable=False)
    facility_ratings = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Feedback {self.id}>'

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        new_feedback = Feedback(
            department=form.department.data,
            year=form.year.data,
            course_ratings=json.dumps(form.course_ratings.data),
            faculty_ratings=json.dumps(form.faculty_ratings.data),
            facility_ratings=json.dumps(form.facility_ratings.data)
        )
        db.session.add(new_feedback)
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('index'))
    return render_template('feedback.html', form=form)

@app.route('/sentiment')
def sentiment():
    return render_template('sentiment.html')

@app.route('/api/sentiment')
def get_sentiment():
    department = request.args.get('department')
    year = request.args.get('year')
    
    if not department or not year:
        return jsonify({'error': 'Missing department or year'}), 400

    feedbacks = Feedback.query.filter_by(department=department, year=int(year)).all()

    def calculate_sentiment(ratings):
        ratings = [int(r) for r in ratings]
        positive = sum(1 for r in ratings if r >= 4)
        negative = sum(1 for r in ratings if r <= 2)
        neutral = len(ratings) - positive - negative
        return {'positive': positive, 'neutral': neutral, 'negative': negative}

    sentiment_data = {
        'courses': calculate_sentiment([r for f in feedbacks for r in json.loads(f.course_ratings)]),
        'faculty': calculate_sentiment([r for f in feedbacks for r in json.loads(f.faculty_ratings)]),
        'facilities': calculate_sentiment([r for f in feedbacks for r in json.loads(f.facility_ratings)])
    }

    return jsonify(sentiment_data)

@app.route('/export_sentiment')
def export_sentiment():
    department = request.args.get('department')
    year = request.args.get('year')
    
    if not department or not year:
        return jsonify({'error': 'Missing department or year'}), 400

    feedbacks = Feedback.query.filter_by(department=department, year=int(year)).all()

    def calculate_sentiment(ratings):
        ratings = [int(r) for r in ratings]
        positive = sum(1 for r in ratings if r >= 4)
        negative = sum(1 for r in ratings if r <= 2)
        neutral = len(ratings) - positive - negative
        return {'positive': positive, 'neutral': neutral, 'negative': negative}

    sentiment_data = {
        'courses': calculate_sentiment([r for f in feedbacks for r in json.loads(f.course_ratings)]),
        'faculty': calculate_sentiment([r for f in feedbacks for r in json.loads(f.faculty_ratings)]),
        'facilities': calculate_sentiment([r for f in feedbacks for r in json.loads(f.facility_ratings)])
    }

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Sentiment Analysis Report - {department.upper()} Year {year}", styles['Title']))

    data = [['Category', 'Positive', 'Neutral', 'Negative']]
    for category, values in sentiment_data.items():
        data.append([category.capitalize(), values['positive'], values['neutral'], values['negative']])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        attachment_filename=f'sentiment_analysis_{department}_{year}.pdf',
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    app.run(debug=True)

