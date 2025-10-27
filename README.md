# Auckland Council CPU/CCC Automation Toolkit

This project implements a command-line assistant that collects applicant data, validates
supporting documents, and drives the myAUCKLAND portal using Playwright to submit
Certificate for Public Use (CPU) or Code Compliance Certificate (CCC) applications.

## Features

- Interactive or JSON-driven data capture for CPU/CCC applications.
- Validation of supporting PDF documents against Auckland Council rules (format, size,
  encryption status).
- Guided Playwright automation that navigates to the appropriate online form, populates
  required fields, and pauses for manual intervention when credentials or payments are
  required.
- Modular architecture so that navigation selectors and data fields can be updated easily
  when the Council portal changes.

## Project Structure

```
src/auckland_automation/
├── cli.py                 # Typer entrypoint
├── data_models.py         # Pydantic models for application payloads
├── document_management.py # PDF validation helpers
├── enums.py               # Application type enumeration
├── input_collection.py    # Interactive data capture routines
├── portal_automation.py   # Playwright automation helpers
└── workflow.py            # High level orchestration
```

## Getting Started

1. **Install dependencies**

   ```bash
   pip install .
   playwright install chromium
   ```

2. **Prepare your documents**

   Ensure each PDF is unlocked, under 300 MB, and follows Auckland Council naming
   conventions (e.g., `RoT.pdf`, `Fire_Report.pdf`).

3. **Run the automation**

   ```bash
   auckland-automation run \
     --type ccc \
     --document /path/to/RoT.pdf \
     --document /path/to/Plan.pdf
   ```

   The CLI will validate your files, prompt for any remaining data, launch a Chromium
   instance, and pause when manual input (login, MFA, payments) is required.

4. **Optional JSON input**

   Provide a JSON file with fields that match the models in `data_models.py` to avoid
   interactive prompts:

   ```bash
   auckland-automation run --type cpu --data-file ./cpu_payload.json --document ./Plan.pdf
   ```

## Security Notes

- Credentials and payment details are never stored. The automation pauses so that the
  user can enter them directly into the myAUCKLAND portal.
- Logging avoids printing sensitive values; enable `--verbose` only when troubleshooting.

## Testing

Create dummy PDFs (unencrypted and under the size limit) to exercise the validation and
portal upload steps without submitting a live application.
