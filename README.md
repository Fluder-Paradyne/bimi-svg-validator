# BIMI SVG Validator

Simple browser tool to check whether an SVG is suitable for use with [BIMI](https://bimigroup.org/) (Brand Indicators for Message Identification).

Validation runs entirely in the browser with **JavaScript + libxml2 WebAssembly** (`xmllint-wasm`), using the official SVG Tiny PS / BIMI **RELAX NG** schema (`validate.rng`). No Python, Pyodide, or server backend.

## Run locally

Serve the folder over HTTP (ES modules and `fetch` need a real origin, not `file://`):

```bash
python3 -m http.server 8080
# or: npx serve .
```

Open `http://localhost:8080/`.

## How it works

1. `index.html` — UI (upload file or paste SVG)
2. `main.js` — loads `validate.rng`, then validates with `xmllint-wasm` (`extension: "relaxng"`)
3. `vendor/xmllint-wasm/` — vendored **xmllint-wasm 5.2.0** (~800 KB total, vs multi‑MB Pyodide previously); MIT license in `vendor/xmllint-wasm/COPYING`, pin/refresh notes in `vendor/xmllint-wasm/VERSION`
4. `validate.rnc` / `validate.rng` — schema source and XML form

## Example SVGs

| File | Expected result | Why |
|------|-----------------|-----|
| [`examples/valid-bimi.svg`](examples/valid-bimi.svg) | Pass | `version="1.2"`, `baseProfile="tiny-ps"`, required `<title>`, `viewBox` (recommended for BIMI), only allowed shapes |
| [`examples/invalid-bimi.svg`](examples/invalid-bimi.svg) | Fail | `<script>`, external `<image>`, animation — not permitted in BIMI/SVG Tiny PS |

Paste either into the tool (or upload the file) to verify the validator.

## References

- [SVG Tiny Portable/Secure (IETF draft)](https://datatracker.ietf.org/doc/id/draft-svg-tiny-ps-abrotman-00.txt)
- [Using the RNC schema to validate BIMI SVG images](https://bimigroup.org/using-the-rnc-schema-to-validate-bimi-svg-images/)
- [xmllint-wasm](https://github.com/noppa/xmllint-wasm)
