#!/usr/bin/python

from flask import request, send_file, render_template, flash, url_for, redirect, Blueprint

import lament_mod.character as character
import lament_mod.tools as tools
import lament_mod.spells as spells
from fdfgen import forge_fdf
from PyPDF2 import PdfFileMerger, PdfFileReader
import subprocess
import os
import glob
import tempfile
import random

# Some sass for the title of the page.
SASS = [
    "All these guys are gonna die anyway",
    "A 1 is good, right?",
    "HOW many hit points?",
    "No, I'm sure those spells will be useful",
    "Don't get too attached",
    """The last 13 guys? They didn't have what it takes.
         But you? YOU'VE got the stuff.""",
    "Intelligence 8? This character is just like you!",
    "Old age looked boring anyway",
]

# Custom error messages for user input. This might need to be an Enum at some point?
ERROR_MESSAGES = {
    "TYPE": "Put some NUMBERS in there, you degenerate.",
    "LURVS": """I love you with all my heart, Moxxi.
     Even in code. Forever and always.""",
    "NEGATIVE": """Really. You'd like NEGATIVE %s characters.
     Uh huh. Lemme get right on that.""",
    "ZERO": """There you go! I generated NO characters for you,
      just like you asked.""",
}

# The path to the blank fillable character sheet PDF.
FILLABLE_CHARACTER_SHEET = os.path.join(
    os.path.dirname(__file__), "LotFPCharacterSheetLastGaspFillable.pdf"
)
# The final directory in which to place the finished PDF, relative to the current
# working directory.
FINAL_PDF_DIRECTORY_NAME = "FinalPDF"

# Whether or not to calculate encumbrance values for the generated characters.
CALCULATE_ENCUMBRANCE = True

# The request argument containing the desired level of character.
REQUEST_ARG_LEVEL = "desired_level"
# The request argument containing the desired class of character.
REQUEST_ARG_CLASS = "desired_class"
# The request argument containing the desired number of generated characters.
REQUEST_ARG_NUM_CHARS = "randos"

lamentApp = Blueprint("lament", __name__)


# @lamentApp.route('/')
@lamentApp.route("/character")
def index():
    """
    The main page for Lament, containing the form for generating characters.
    """
    return render_template("lament/lament.html", sass=random.choice(SASS))


@lamentApp.route("/lament", methods=["GET", "POST"])
def lament_pdf():
    """
    Generate the desired number of characters using the desired class and level data
    from the request.
    """
    try:
        desired_level, desired_class, number = handle_input(request.form)
    except (TypeError, ValueError):
        # Lament has custom error messages because I'm a nerd, so garbage input is
        # handled in its own function.
        message = handle_error(request.form[REQUEST_ARG_NUM_CHARS], is_type_error=True)
        # Flash the error message(s) and redirect to the main app page.
        flash(message)
        return redirect(url_for("lament.index"))

    if number <= 0:
        # There are also custom error messages for numbers that are too high or too low.
        message = handle_error(number)
        flash(message)
        return redirect(url_for("lament.index"))

    # We'll use a temporary directory to hold the individual generated PDFs before
    # we merge them into the final document.
    tmpdir = tempfile.TemporaryDirectory(dir=os.getcwd())

    # Grab character data from the API and fill it into individual character sheets.
    generate_individual_chars(number, tmpdir, desired_class, desired_level)

    if desired_class:
        final_name = os.path.join("FinalPDF", desired_class + ".pdf")
    else:
        final_name = os.path.join("FinalPDF", str(number) + "Characters.pdf")

    # Create a directory for the final PDF, deleting any conflicting PDFs.
    prep_directory(final_name)

    # Merge all the individual PDFs into one final PDF.
    mergePDFs(tmpdir.name, final_name)

    return send_file(
        final_name,
        mimetype="application/pdf",
        as_attachment=True,
        attachment_filename=final_name,
    )


def handle_input(form):
    """
    Sanitize and handle the input from the form. Returns the desired character level,
    the desired character class, and the desired number of characters.
    """
    desired_level = int(form[REQUEST_ARG_LEVEL])

    # If they asked for a specific character class, we know we're only generating one
    # character.
    if REQUEST_ARG_CLASS in form.keys():
        desired_class = form[REQUEST_ARG_CLASS]
        number = 1

    else:
        number = int(form[REQUEST_ARG_NUM_CHARS])
        desired_class = None

    # Sanity check - we'll make sure not to generate more than 20 characters at once.
    if number > 20:
        number = 1

    # I'm sure there's a better way to get these three values (they could all be handled
    # by separate functions, I suppose), but the 3-tuple works for now.
    return (desired_level, desired_class, number)


def handle_error(number, is_type_error=False):
    """
    Generate custom error messages for various errors, including input that is not an
    integer and input <= 0. Returns a message to flash before redirect.
    """
    if is_type_error:
        message = ERROR_MESSAGES["TYPE"]

        if number in ("lurvs", "Lurvs"):
            message = ERROR_MESSAGES["LURVS"]
    else:
        # If it's not a type error, we know we've received a number <= 0.
        if number < 0:
            message = ERROR_MESSAGES["NEGATIVE"] % abs(number)
        else:
            message = ERROR_MESSAGES["ZERO"]

    return message


def generate_individual_chars(num_characters, temp_directory, char_class, char_level):
    """
    Generate individual character sheets and fill their form fields with data. Writes
    them to the given temporary directory.
    """
    for i in range(num_characters):
        if char_class:
            PC = character.LotFPCharacter(
                char_class,
                char_level,
                calculate_encumbrance=CALCULATE_ENCUMBRANCE,
                counter=i,
            )
        else:
            PC = character.LotFPCharacter(
                desired_class=None,
                desired_level=char_level,
                calculate_encumbrance=CALCULATE_ENCUMBRANCE,
                counter=i,
            )

        # If the character has spells, create a PDF spell sheet and fill
        # it with spells and spell info.
        if PC.is_spellcaster():
            spells.create_spellsheet_pdf(
                PC.details, PC.name, filename=None, directory=temp_directory.name
            )

        # Create fdf data files to fill PDF form fields
        fdf_data = forge_fdf("", PC.details, [], [], [])

        with open(os.path.join(temp_directory.name, PC.fdf_name), "wb") as f:
            f.write(fdf_data)

        run_pdftk(PC, temp_directory.name)


def run_pdftk(character, tempdir_name):
    """
    Run pdftk as a subprocess, filling the form fields of the PDFs with FDF data and
    storing the resulting PDFs in the given temporary directory.
    """
    path_to_pdftk = tools.get_pdftk_path()

    # All of the command-line arguments for PDFtk,
    # since they were getting kinda long.
    args = [
        path_to_pdftk,
        FILLABLE_CHARACTER_SHEET,
        "fill_form",
        character.fdf_name,
        "output",
        character.filled_name,
        "flatten",
    ]

    # Fill the forms with PDFtk, store them in the tempfiles directory.
    subprocess.run(args, cwd=tempdir_name, **tools.subprocess_args(False))


def prep_directory(final_PDF_name):
    """
    Create a directory on disk for the final PDF. If the directory already exists,
    it will be cleared of any PDFs with a conflicting name.
    """
    try:
        os.mkdir(FINAL_PDF_DIRECTORY_NAME)
    except FileExistsError:
        # If the directory already exists, all we need to do is remove any PDFs with
        # conflicting names.
        pass

    # Remove any conflicting final PDFs.
    if os.path.exists(final_PDF_name):
        os.remove(final_PDF_name)


def mergePDFs(tempdir_name, final_PDF_name):
    """
    Merge all files ending in .pdf in the given temporary directory into a single
    PDF. Writes the final PDF back into the given temporary directory.
    """
    merger = PdfFileMerger()
    PDFs_to_be_merged = glob.glob(os.path.join(tempdir_name, "*.pdf"))

    # Sort the PDFs so they show up in the correct order in the final document.
    PDFs_to_be_merged.sort()

    for PDF in PDFs_to_be_merged:
        with open(PDF, "rb"):
            merger.append(PdfFileReader(PDF))

    merger.write(final_PDF_name)
