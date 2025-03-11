from lxml import etree
from js import document, FileReader
from pyodide.ffi import create_proxy

# Global variable to store the compiled schema
relaxng = None


# Initialize the schema once during load
def init_schema():
    global relaxng
    try:
        with open("validate.rng", "r") as f:
            relaxng_doc = etree.parse(f)
            relaxng = etree.RelaxNG(relaxng_doc)
        return True
    except Exception as e:
        document.getElementById("result").innerHTML = f"Schema initialization error: {str(e)}"
        document.getElementById("result").className = "result error"
        return False


# Function to validate SVG
def validate_svg(svg_content):
    try:
        doc = etree.fromstring(svg_content.encode('utf-8') if isinstance(svg_content, str) else svg_content)
        is_valid = relaxng.validate(doc)

        if is_valid:
            return True, "SVG is valid!"
        else:
            error_message = relaxng.error_log.last_error
            return False, f"Validation failed: {error_message}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def validate_file(event):
    result_div = document.getElementById("result")
    result_div.innerHTML = "Processing..."
    result_div.className = "result"

    file = document.getElementById("svg-file").files.item(0)
    if not file:
        result_div.innerHTML = "Please select a file first."
        result_div.className = "result error"
        return

    reader = FileReader.new()
    reader.onload = create_proxy(lambda e: handle_validation_result(validate_svg(e.target.result)))
    reader.readAsText(file)


def validate_content(event):
    content = document.getElementById("svg-content").value
    if not content.strip():
        handle_validation_result((False, "Please enter SVG content."))
        return
    handle_validation_result(validate_svg(content))


def handle_validation_result(result):
    success, message = result
    result_div = document.getElementById("result")
    result_div.innerHTML = message
    result_div.className = "result success" if success else "result error"


# Set up event handlers
if init_schema():
    document.getElementById("validate-file-btn").addEventListener("click", create_proxy(validate_file))
    document.getElementById("validate-content-btn").addEventListener("click", create_proxy(validate_content))