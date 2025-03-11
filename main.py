import os
from lxml import etree
import tempfile
import subprocess
from js import document, FileReader, console
from pyodide.ffi import create_proxy


# Function to validate SVG with pyjing
def validate_svg(svg_path):
    try:
        # Load the RNG schema
        with open("validate.rng", "r") as f:
            relaxng_doc = etree.parse(f)
            relaxng = etree.RelaxNG(relaxng_doc)

        # Parse the SVG file
        doc = etree.parse(svg_path)

        # Validate against the schema
        is_valid = relaxng.validate(doc)

        if is_valid:
            return True, "SVG is valid!"
        else:
            # Get validation errors
            errors = relaxng.error_log.filter_from_errors()
            error_message = "\n".join([str(error) for error in errors])
            return False, f"Validation failed: {error_message}"
    except Exception as e:
        return False, f"Error: {str(e)}"

# Function to handle file validation
def validate_file(event):
    result_div = document.getElementById("result")
    result_div.innerHTML = "Processing..."
    result_div.className = "result"

    file_input = document.getElementById("svg-file")
    if file_input.files.length == 0:
        result_div.innerHTML = "Please select a file first."
        result_div.className = "result error"
        return

    file = file_input.files.item(0)

    # Create a FileReader to read the file
    reader = FileReader.new()

    def on_load(event):
        try:
            # Get the file content as text
            content = event.target.result

            # Create a temporary file to save the SVG content
            with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
                tmp_path = tmp.name
                # If content is a string, encode it, otherwise use it as is
                if isinstance(content, str):
                    tmp.write(content.encode('utf-8'))
                else:
                    tmp.write(content)

            # Validate the SVG
            success, message = validate_svg(tmp_path)

            # Update the result display
            if success:
                result_div.innerHTML = message
                result_div.className = "result success"
            else:
                result_div.innerHTML = message
                result_div.className = "result error"

            # Clean up the temporary file
            os.unlink(tmp_path)

        except Exception as e:
            console.error(str(e))
            result_div.innerHTML = f"Error: {str(e)}"
            result_div.className = "result error"

    # Set up the onload callback and read the file
    reader.onload = create_proxy(on_load)
    reader.readAsText(file)  # Read as text instead of binary


# Function to handle content validation
def validate_content(event):
    result_div = document.getElementById("result")
    result_div.innerHTML = "Processing..."
    result_div.className = "result"

    content = document.getElementById("svg-content").value
    if not content.strip():
        result_div.innerHTML = "Please enter SVG content."
        result_div.className = "result error"
        return

    try:
        # Create a temporary file to save the SVG content
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(content.encode('utf-8'))

        # Validate the SVG
        success, message = validate_svg(tmp_path)

        # Update the result display
        if success:
            result_div.innerHTML = message
            result_div.className = "result success"
        else:
            result_div.innerHTML = message
            result_div.className = "result error"

        # Clean up the temporary file
        os.unlink(tmp_path)

    except Exception as e:
        console.error(str(e))
        result_div.innerHTML = f"Error: {str(e)}"
        result_div.className = "result error"


# Attach event handlers to buttons
validate_file_proxy = create_proxy(validate_file)
validate_content_proxy = create_proxy(validate_content)

document.getElementById("validate-file-btn").addEventListener("click", validate_file_proxy)
document.getElementById("validate-content-btn").addEventListener("click", validate_content_proxy)

print("SVG Validator initialized. Upload a file or paste SVG content to validate.")