import { validateXML } from "./vendor/xmllint-wasm/index-browser.mjs";

/** @type {string | null} */
let schemaContents = null;

/** @type {Promise<string> | null} */
let schemaLoadPromise = null;

/** Incremented on each user validation; only the latest run may update the UI. */
let latestValidationToken = 0;

/** @type {HTMLButtonElement | null} */
let fileBtn = null;

/** @type {HTMLButtonElement | null} */
let contentBtn = null;

const SMOKE_SVG = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.2" baseProfile="tiny-ps" viewBox="0 0 1 1">
  <title>init</title>
</svg>`;

/**
 * @returns {HTMLElement | null}
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
  if (!el) {
    console.error("Missing #result element");
    return;
  }
  el.textContent = message;
  el.className = className;
}

/**
 * @param {boolean} disabled
 */
function setButtonsDisabled(disabled) {
  if (fileBtn) fileBtn.disabled = disabled;
  if (contentBtn) contentBtn.disabled = disabled;
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
 * @param {unknown} err
 * @returns {string}
 */
function formatValidationError(err) {
  const message = err instanceof Error ? err.message : String(err);
  if (/abort|out of memory|memory|OOM/i.test(message)) {
    return (
      "Error: Validator ran out of memory or aborted. " +
      "Try a smaller SVG, another browser, or refresh the page."
    );
  }
  return `Error: ${message}`;
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
      // Schema is large; allow growth up to ~128 MiB without reserving it all upfront.
      initialMemoryPages: 256,
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
    return { ok: false, message: formatValidationError(err) };
  }
}

/**
 * @param {{ ok: boolean, message: string }} outcome
 */
function showOutcome(outcome) {
  setResult(outcome.message, outcome.ok ? "result success" : "result error");
}

async function handleValidateFile() {
  const token = ++latestValidationToken;
  setButtonsDisabled(true);
  setResult("Processing...");

  const fileInput = /** @type {HTMLInputElement | null} */ (
    document.getElementById("svg-file")
  );
  if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
    if (token === latestValidationToken) {
      setResult("Please select a file first.", "result error");
    }
    setButtonsDisabled(false);
    return;
  }

  const file = fileInput.files[0];
  try {
    const content = await file.text();
    const outcome = await validateSvg(content);
    if (token !== latestValidationToken) return;
    showOutcome(outcome);
  } catch (err) {
    if (token !== latestValidationToken) return;
    setResult(formatValidationError(err), "result error");
  } finally {
    if (token === latestValidationToken) {
      setButtonsDisabled(false);
    }
  }
}

async function handleValidateContent() {
  const token = ++latestValidationToken;
  setButtonsDisabled(true);
  setResult("Processing...");

  const textarea = /** @type {HTMLTextAreaElement | null} */ (
    document.getElementById("svg-content")
  );
  const content = textarea ? textarea.value : "";

  if (!content.trim()) {
    if (token === latestValidationToken) {
      setResult("Please enter SVG content.", "result error");
    }
    setButtonsDisabled(false);
    return;
  }

  try {
    const outcome = await validateSvg(content);
    if (token !== latestValidationToken) return;
    showOutcome(outcome);
  } catch (err) {
    if (token !== latestValidationToken) return;
    setResult(formatValidationError(err), "result error");
  } finally {
    if (token === latestValidationToken) {
      setButtonsDisabled(false);
    }
  }
}

async function init() {
  fileBtn = /** @type {HTMLButtonElement | null} */ (
    document.getElementById("validate-file-btn")
  );
  contentBtn = /** @type {HTMLButtonElement | null} */ (
    document.getElementById("validate-content-btn")
  );
  const resultEl = getResultEl();

  if (!fileBtn || !contentBtn || !resultEl) {
    console.error(
      "SVG Validator: missing required DOM elements (#validate-file-btn, #validate-content-btn, #result)."
    );
    return;
  }

  setButtonsDisabled(true);
  setResult("Loading validator…");

  try {
    await loadSchema();
    setResult("Compiling validator (first run)…");
    // Exercise WASM/worker + schema compile once so failures surface at init.
    const smoke = await validateSvg(SMOKE_SVG);
    if (!smoke.ok) {
      throw new Error(
        smoke.message.replace(/^Validation failed:\n?/, "") ||
          "Smoke validation did not succeed."
      );
    }

    fileBtn.addEventListener("click", () => {
      void handleValidateFile();
    });
    contentBtn.addEventListener("click", () => {
      void handleValidateContent();
    });
    setButtonsDisabled(false);
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
