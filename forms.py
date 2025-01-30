from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FieldList, SelectField
from wtforms.validators import DataRequired, NumberRange

class FeedbackForm(FlaskForm):
    department = SelectField('Department', choices=[('cs', 'Computer Science'), ('ee', 'Electrical Engineering'), ('me', 'Mechanical Engineering')], validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=1, max=4)])
    course_ratings = FieldList(IntegerField('Course Rating', validators=[DataRequired(), NumberRange(min=0, max=5)]), min_entries=5, max_entries=5)
    faculty_ratings = FieldList(IntegerField('Faculty Rating', validators=[DataRequired(), NumberRange(min=0, max=5)]), min_entries=5, max_entries=5)
    facility_ratings = FieldList(IntegerField('Facility Rating', validators=[DataRequired(), NumberRange(min=0, max=5)]), min_entries=5, max_entries=5)

