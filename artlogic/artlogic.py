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

    # If the submit button is clicked and the form validates, we'll handle
    # the data (converting between strings and integers as necessary) and
    # return the same page with the output.
    if form.validate_on_submit():
        output = handleData(form.data['input_data'])
        return redirect(url_for('artlogic.index', output=output))

    # If the submit button hasn't been clicked, we'll just return the page
    # with whatever output is currently set (if no data has been submitted
    # previously, the output will be blank).
    return render_template(
        'artlogic/artlogic.html',
        title=TITLE,
        form=form,
        output=request.args.get('output'))


def handleData(data):
    """
    Determine if the data is integers or a string, and encode/decode it.
    Returns a string.
    """
    # Determine if the data is a list of integers by attempting to coerce
    # it to the integer type.
    try:
        encoded_ints = []
        for item in data.split(" "):
            encoded_ints.append(int(item))
        # If this completes without exceptions, we know the data is a list
        # of integers, and we can decode them.
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
            result = str(encoded_ints[0])

        return result
