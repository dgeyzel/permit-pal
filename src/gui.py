import asyncio
from pathlib import Path
from typing import Optional
import time
from nicegui import app, ui
import report

# Theme from permit_pal_banner.png: dark base, \
# teal/rose/lavender accents, white text
PAGE_CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap');
    body, body.body--dark, .nicegui-content {
        background: #282a36 !important;
        color: #ffffff !important;
        font-family: 'Outfit', 'Segoe UI', system-ui, sans-serif !important;
    }
    .permit-pal-page {
        width: 90%;
        max-width: 1200px;
        margin: 0 auto;
        padding: 1.5rem;
    }
    .permit-pal-page .banner-wrapper {
        width: 100%;
        height: 0;
        padding-bottom: 30%;
        position: relative;
        margin-bottom: 1.5rem;
        border-radius: 8px;
        overflow: visible;
    }
    .permit-pal-page .banner-wrapper .permit-pal-banner {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: contain;
        object-position: center;
        border-radius: 8px;
        display: block;
    }
    .permit-pal-page .q-field__control-container,
    .permit-pal-page .q-field__control {
        background: #36384a !important;
        border-radius: 4px;
    }
    .permit-pal-page .q-field--outlined .q-field__control:before {
        border-color: rgba(255,255,255,0.25) !important;
    }
    .permit-pal-page .q-field__label,
    .permit-pal-page .q-field__native,
    .permit-pal-page .q-field__prefix,
    .permit-pal-page .q-field__suffix {
        color: #ffffff !important;
    }
    .permit-pal-page textarea.q-field__native {
        background: #36384a !important;
    }
    .q-menu {
        background: #36384a !important;
    }
    .q-item {
        color: #9ca0b0 !important;
    }
    .q-item.q-item--active {
        color: #ffffff !important;
    }
    .permit-pal-page .q-field--focused .q-field__control:before {
        border-color: #448c8c !important;
        border-width: 2px !important;
    }
    .permit-pal-page .q-field--focused .q-field__label {
        color: #448c8c !important;
    }
    .permit-pal-page .q-btn--unelevated {
        background: #448c8c !important;
        color: #ffffff !important;
    }
    .permit-pal-page .q-btn--unelevated:hover {
        background: #5a9e9e !important;
    }
    .permit-pal-page .q-toggle__label {
        color: #ffffff !important;
    }
    .permit-pal-page .nicegui-markdown {
        color: rgba(255,255,255,0.95) !important;
    }
    .permit-pal-page .nicegui-markdown table {
        border-color: rgba(255,255,255,0.2) !important;
    }
    .permit-pal-page .nicegui-markdown th,
    .permit-pal-page .nicegui-markdown td {
        border-color: rgba(255,255,255,0.2) !important;
        color: #ffffff !important;
    }
    /* Alternating rows and header for markdown tables */
    .permit-pal-page .nicegui-markdown table tr:nth-child(odd) td {
        background: rgba(255,255,255,0.05) !important;
    }
    .permit-pal-page .nicegui-markdown table tr:nth-child(even) td {
        background: rgba(255,255,255,0.02) !important;
    }
    /* Header only: thead row, or first tr when table has no thead (flat trs) */
    .permit-pal-page .nicegui-markdown table thead tr th,
    .permit-pal-page .nicegui-markdown table thead tr td,
    .permit-pal-page .nicegui-markdown table > tr:first-child th,
    .permit-pal-page .nicegui-markdown table > tr:first-child td {
        background: #36384a !important;
    }
"""  # noqa: E501


def create_page() -> None:
    """Create the main Permit Pal web interface.

    The page includes:
      * Banner image (permit_pal_banner.png)
      * Prompt input textarea (first argument to create_report)
      * LLM model dropdown sourced from report.LLM_MODEL
      * RAG enable/disable toggle (controls report.RAG_ENABLED)
      * Generate button to trigger report creation
      * Markdown area to display the generated report table
      * Error display area for validation and runtime errors
    """
    ui.add_css(PAGE_CSS)

    # Zebra striping for markdown tables
    # (use nicegui-markdown class per NiceGUI docs)
    ui.add_head_html("""
        <style>
            .nicegui-markdown table tr:nth-child(even) td {
                background-color: rgba(255,255,255,0.02) !important;
            }
            .nicegui-markdown table tr:nth-child(odd) td {
                background-color: rgba(255,255,255,0.05) !important;
            }
            .nicegui-markdown table thead tr th,
            .nicegui-markdown table thead tr td,
            .nicegui-markdown table > tr:first-child th,
            .nicegui-markdown table > tr:first-child td {
                background-color: #36384a !important;
            }
        </style>
    """)

    with ui.column().classes("permit-pal-page"):
        with ui.element("div").classes("banner-wrapper"):
            ui.image("/assets/permit_pal_banner.png").classes(
                "permit-pal-banner"
            )

        prompt_input = ui.textarea(
            label="Describe what you want to accomplish and where",
            placeholder="I want to open a restaurant in Atlanta, Georgia.",
        ).classes("w-full").props('input-style=height:30px')

        default_model: Optional[str] = (
            report.LLM_MODEL[0] if report.LLM_MODEL else None
        )
        model_select = ui.select(
            options=report.LLM_MODEL,
            label="LLM model",
            value=default_model,
        ).classes("w-full")

        rag_toggle = ui.switch("Enable RAG", value=False)

        error_label = ui.label("").style("color: #e8a0b4")

        generating_label = ui.label("").style("color: #9ca0b0")

        generate_button = ui.button("Generate report")

        result_markdown = ui.markdown("")

        async def handle_generate() -> None:
            """Handle clicks on the Generate report button."""
            error_label.text = ""
            result_markdown.set_content("")

            prompt = (prompt_input.value or "").strip()
            if not prompt:
                error_label.text = (
                    "Please enter a description before generating a report."
                )
                return

            model = model_select.value
            if model is None:
                error_label.text = "Please select an LLM model."
                return

            if model not in report.LLM_MODEL:
                error_label.text = "Invalid LLM model selected."
                return

            generate_button.disable()
            generating_label.text = "Generating report..."
            await asyncio.sleep(0)

            try:
                report.RAG_ENABLED = bool(rag_toggle.value)
                print("Starting report generation from the UI.")
                start = time.perf_counter()
                output_table = await report.create_report(prompt, model)
                end = time.perf_counter()
                print(f"Report generation time from the UI: "
                      f"{end - start:.2f} seconds.")
                if not output_table:
                    error_label.text = "The model returned an empty response."
                    result_markdown.set_content("")
                else:
                    result_markdown.set_content(output_table)
                    await asyncio.sleep(0)
            except Exception:
                error_label.text = (
                    "An error occurred while generating the report. "
                    "Please check your configuration and try again."
                )
                result_markdown.set_content("")
            finally:
                generating_label.text = ""
                generate_button.enable()

        generate_button.on("click", handle_generate)


def main() -> None:
    """Run the NiceGUI web application."""
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    if assets_dir.is_dir():
        app.add_static_files("/assets", str(assets_dir))
    create_page()
    ui.run(title="Permit Pal", reload=False)


if __name__ == "__main__":
    main()
