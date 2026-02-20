import asyncio
from typing import Optional
import time
from nicegui import ui
import report


def create_page() -> None:
    """Create the main Permit Pal web interface.

    The page includes:
      * Prompt input textarea (first argument to create_report)
      * LLM model dropdown sourced from report.LLM_MODEL
      * RAG enable/disable toggle (controls report.RAG_ENABLED)
      * Generate button to trigger report creation
      * Markdown area to display the generated report table
      * Error display area for validation and runtime errors
    """
    ui.markdown("# Permit Pal Report Generator")

    prompt_input = ui.textarea(
        label="Describe what you want to accomplish and where",
        placeholder="I want to open a restaurant in Atlanta, Georgia."
    ).classes("w-full")

    default_model: Optional[str] = (
        report.LLM_MODEL[0] if report.LLM_MODEL else None
    )
    model_select = ui.select(
        options=report.LLM_MODEL,
        label="LLM model",
        value=default_model,
    ).classes("w-full")

    rag_toggle = ui.switch("Enable RAG", value=False)

    error_label = ui.label("").style("color: red")

    generating_label = ui.label("").style("color: gray")

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
        # Yield so the "Generating report..." update is sent
        await asyncio.sleep(0)

        try:
            report.RAG_ENABLED = bool(rag_toggle.value)
            print("Starting report generation from the UI.")
            start = time.perf_counter()
            output_table = await report.create_report(prompt, model)
            end = time.perf_counter()
            print(f"Report generation time from the UI: \
                {end - start:.2f} seconds.")
            if not output_table:
                error_label.text = "The model returned an empty response."
                result_markdown.set_content("")
            else:
                result_markdown.set_content(output_table)
                # Yield so the table update is sent to the client
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
    create_page()
    ui.run(title="Permit Pal", reload=False)


if __name__ == "__main__":
    main()
