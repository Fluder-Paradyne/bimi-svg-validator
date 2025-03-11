from lxml import etree
import tempfile
import os
from js import document, FileReader, console
from pyodide.ffi import create_proxy
from functools import lru_cache


# Cache the RNG schema to avoid reloading it for each validation
@lru_cache(maxsize=1)
def get_relaxng_validator():
    with open("validate.rng", "r") as f:
        relaxng_doc = etree.parse(f)
        return etree.RelaxNG(relaxng_doc)


# Function to validate SVG
def validate_svg(svg_path):
    try:
        # Get the cached validator
        relaxng = get_relaxng_validator()

        # Parse the SVG file
        doc = etree.parse(svg_path)

        # Validate against the schema
        is_valid = relaxng.validate(doc)

        if is_valid:
            return True, "SVG is valid!"
        else:
            # Get validation errors efficiently
            error_message = "\n".join(
                str(error) for error in relaxng.error_log.filter_from_errors()
            )
            return False, f"Validation failed: {error_message}"
    except Exception as e:
        return False, f"Error: {str(e)}"


# Update the UI with validation results
def update_result(success, message):
    result_div = document.getElementById("result")
    result_div.innerHTML = message
    result_div.className = f"result {'success' if success else 'error'}"


# Function to validate content from either file or text input
def validate_content_from_string(content):
    try:
        # Create a temporary file in memory when possible
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            tmp_path = tmp.name
            if isinstance(content, str):
                tmp.write(content.encode("utf-8"))
            else:
                tmp.write(content)

        # Validate the SVG
        success, message = validate_svg(tmp_path)

        # Clean up the temporary file
        os.unlink(tmp_path)

        return success, message
    except Exception as e:
        console.error(str(e))
        return False, f"Error: {str(e)}"


# File validation handler
def validate_file(event):
    result_div = document.getElementById("result")
    result_div.innerHTML = "Processing..."
    result_div.className = "result"

    file_input = document.getElementById("svg-file")
    if file_input.files.length == 0:
        update_result(False, "Please select a file first.")
        return

    file = file_input.files.item(0)
    reader = FileReader.new()

    def on_load(event):
        content = event.target.result
        success, message = validate_content_from_string(content)
        update_result(success, message)

    reader.onload = create_proxy(on_load)
    reader.readAsText(file)


# Text content validation handler
def validate_content(event):
    result_div = document.getElementById("result")
    result_div.innerHTML = "Processing..."
    result_div.className = "result"

    content = document.getElementById("svg-content").value
    if not content.strip():
        update_result(False, "Please enter SVG content.")
        return

    success, message = validate_content_from_string(content)
    update_result(success, message)


# Set up event handlers (only once)
validate_file_proxy = create_proxy(validate_file)
validate_content_proxy = create_proxy(validate_content)

document.getElementById("validate-file-btn").addEventListener(
    "click", validate_file_proxy
)
document.getElementById("validate-content-btn").addEventListener(
    "click", validate_content_proxy
)

print("SVG Validator initialized. Upload a file or paste SVG content to validate.")
