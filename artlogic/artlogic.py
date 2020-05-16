#!/usr/bin/python

from flask import Blueprint, redirect, render_template, request, url_for
import artlogic.encode as encode
import artlogic.forms as forms


TITLE = "Art & Logic Programming Challenge"

artlogicApp = Blueprint('artlogic', __name__)


@artlogicApp.route('/artlogic', methods=['GET', 'POST'])
def index():
    """
    The Art & Logic Programming Challenge webapp, with a form for input data
    and a place to display output.
    """
    form = forms.ArtLogicForm()

    if form.validate_on_submit():
        output = handleData(form.data['input_data'])
        return redirect(url_for('artlogic.index', output=output))

    return render_template(
        'artlogic/artlogic.html',
        title=TITLE,
        form=form,
        output=request.args.get('output'))


def handleData(data):
    """
    Determine if the data is integers or a string, and encode/decode it.
    """
    # Determine if the data is a list of integers by attempting to coerce
    # it to the integer type.
    try:
        for item in data.split(" "):
            int(item)
        # If this completes without exceptions, we know the data is a list
        # of integers, and we can decode them.
        encoded_ints = data.split(" ")
        encoded_ints = [int(item) for item in encoded_ints]

        return encode.decode(encoded_ints)

    # If coercing the data to an integer throws an exception, then we know
    # it's a string, and we can encode it.
    except ValueError:
        encoded_ints = encode.encode(data)

        # If the string was over 4 characters, it was encoded into more than
        # one integer, so we need to join them into a string for display.
        if len(encoded_ints) > 1:
            int_strings = [str(item) for item in encoded_ints]
            result = ' '.join(int_strings)
        else:
            # If it's only one integer, we can display it as is.
            result = encoded_ints

        return result
