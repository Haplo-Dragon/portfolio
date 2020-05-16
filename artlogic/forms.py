from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class ArtLogicForm(FlaskForm):
    """
    A form for converting strings to 32-bit encoded integers (and vice versa)
    according to the Art & Logic Programming Challenge specification.
    """
    input_data = StringField("String/Integer(s) to encode/decode", [
        DataRequired()])
    submit = SubmitField('Submit')
