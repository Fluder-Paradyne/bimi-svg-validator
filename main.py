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
    global relaxng

    try:
        # Parse the SVG content directly from string
        doc = etree.fromstring(svg_content.encode('utf-8') if isinstance(svg_content, str) else svg_content)

        # Validate against the schema
        is_valid = relaxng.validate(doc)

        if is_valid:
            return True, "SVG is valid!"
        else:
            # Get validation errors
            error_message = "\n".join([str(error) for error in relaxng.error_log.filter_from_errors()])
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
    reader = FileReader.new()

    def on_load(event):
        content = event.target.result
        success, message = validate_svg(content)

        if success:
            result_div.innerHTML = message
            result_div.className = "result success"
        else:
            result_div.innerHTML = message
            result_div.className = "result error"

    reader.onload = create_proxy(on_load)
    reader.readAsText(file)


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

    success, message = validate_svg(content)

    if success:
        result_div.innerHTML = message
        result_div.className = "result success"
    else:
        result_div.innerHTML = message
        result_div.className = "result error"


# Initialize and set up event handlers
if init_schema():
    document.getElementById("validate-file-btn").addEventListener("click", create_proxy(validate_file))
    document.getElementById("validate-content-btn").addEventListener("click", create_proxy(validate_content))
    print("SVG Validator initialized. Upload a file or paste SVG content to validate.")