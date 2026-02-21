import asyncio
import report

"""This file is used to test the application logic \
    without running the web GUI.
It is not used in the production application.
"""

# List of test prompts
TEST_PROMPT = [
    'I want to open a restaurant in Atlanta, Georgia.',
    'I want to open a restaurant in San Diego, CA.',
    'I want to remodel a historic home in Atlanta, GA.',
    'I want to become a barber in New York City, NY',
    'I want to become a barber in Topeka, Kansas'
]


async def test_run(prompt: str, llm_model: str, rag_enabled):
    """Function for doing tests of the application logic in main()
    """
    report.RAG_ENABLED = rag_enabled
    output_table = await report.create_report(prompt, llm_model)
    print("Final Report Output:\n" + output_table)


async def main():
    await test_run(TEST_PROMPT[1], report.LLM_MODEL[7], False)

asyncio.run(main())
