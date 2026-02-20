import asyncio
import report


# List of test prompts
TEST_PROMPT = [
    'I want to open a restaurant in Atlanta, Georgia.',
    'I want to open a restaurant in San Diego, CA.',
    'I want to remodel a historic home in Atlanta, GA.',
    'I want to become a barber in New York City, NY',
    'I want to become a barber in Topeka, Kansas'
]


async def test_run(prompt: str, llm_model: str, rag_enabled):
    report.RAG_ENABLED = rag_enabled
    output_table = await report.create_report(prompt, llm_model)
    print("Final Report Output:\n" + output_table)


async def main():
    await test_run(TEST_PROMPT[1], report.LLM_MODEL[4], True)

asyncio.run(main())
