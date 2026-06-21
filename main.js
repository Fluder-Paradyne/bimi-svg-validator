import { validateXML } from "./vendor/xmllint-wasm/index-browser.mjs";

/** @type {string | null} */
let schemaContents = null;

/** @type {Promise<string> | null} */
let schemaLoadPromise = null;

/**
 * @returns {HTMLElement}
 */
function getResultEl() {
  return document.getElementById("result");
}

/**
 * @param {string} message
 * @param {"result" | "result success" | "result error"} className
 */
function setResult(message, className = "result") {
  const el = getResultEl();
  el.textContent = message;
  el.className = className;
}

/**
 * Load the BIMI / SVG Tiny PS RelaxNG schema once.
 * @returns {Promise<string>}
 */
function loadSchema() {
  if (schemaContents !== null) {
    return Promise.resolve(schemaContents);
  }
  if (!schemaLoadPromise) {
    schemaLoadPromise = fetch("./validate.rng")
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            `Failed to load schema (HTTP ${response.status}). Serve this folder over HTTP, not as a file:// page.`
          );
        }
        return response.text();
      })
      .then((text) => {
        schemaContents = text;
        return text;
      })
      .catch((err) => {
        schemaLoadPromise = null;
        throw err;
      });
  }
  return schemaLoadPromise;
}

/**
 * Validate SVG string against the BIMI RelaxNG schema.
 * @param {string} svgContent
 * @returns {Promise<{ ok: boolean, message: string }>}
 */
async function validateSvg(svgContent) {
  try {
    const schema = await loadSchema();

    const result = await validateXML({
      xml: [
        {
          fileName: "input.svg",
          contents: svgContent,
        },
      ],
      schema: [
        {
          fileName: "validate.rng",
          contents: schema,
        },
      ],
      extension: "relaxng",
      // Schema is large; give libxml2 enough room in the browser worker.
      initialMemoryPages: 512,
      maxMemoryPages: 2048,
    });

    if (result.valid) {
      return { ok: true, message: "SVG is valid!" };
    }

    const errors = (result.errors || [])
      .map((e) => e.message || e.rawMessage)
      .filter(Boolean);

    const detail =
      errors.length > 0
        ? errors.join("\n")
        : result.rawOutput || "Unknown validation error.";

    return { ok: false, message: `Validation failed:\n${detail}` };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, message: `Error: ${message}` };
  }
}

/**
 * @param {{ ok: boolean, message: string }} outcome
 */
function showOutcome(outcome) {
  setResult(outcome.message, outcome.ok ? "result success" : "result error");
}

async function handleValidateFile() {
  setResult("Processing...");

  const fileInput = /** @type {HTMLInputElement} */ (
    document.getElementById("svg-file")
  );
  if (!fileInput.files || fileInput.files.length === 0) {
    setResult("Please select a file first.", "result error");
    return;
  }

  const file = fileInput.files[0];
  try {
    const content = await file.text();
    const outcome = await validateSvg(content);
    showOutcome(outcome);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    setResult(`Error: ${message}`, "result error");
  }
}

async function handleValidateContent() {
  setResult("Processing...");

  const content = /** @type {HTMLTextAreaElement} */ (
    document.getElementById("svg-content")
  ).value;

  if (!content.trim()) {
    setResult("Please enter SVG content.", "result error");
    return;
  }

  const outcome = await validateSvg(content);
  showOutcome(outcome);
}

async function init() {
  const fileBtn = document.getElementById("validate-file-btn");
  const contentBtn = document.getElementById("validate-content-btn");

  fileBtn.disabled = true;
  contentBtn.disabled = true;
  setResult("Loading validator…");

  try {
    await loadSchema();
    fileBtn.addEventListener("click", () => {
      void handleValidateFile();
    });
    contentBtn.addEventListener("click", () => {
      void handleValidateContent();
    });
    fileBtn.disabled = false;
    contentBtn.disabled = false;
    setResult("");
    console.log(
      "SVG Validator initialized. Upload a file or paste SVG content to validate."
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    setResult(`Schema initialization error: ${message}`, "result error");
  }
}

void init();
