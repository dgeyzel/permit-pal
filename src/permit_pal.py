import asyncio
import report
import argparse
import time


"""This file is used to run the application logic \
    without running the web GUI.
It takes input from the command line and runs the application logic.
Output is printed to the console.
Example usage:
python src/permit_pal.py --prompt "I want to open a restaurant in Atlanta, Georgia" --llm_model "gemini-2.5-pro" --rag  # noqa: E501
python src/permit_pal.py --prompt "I want to open a restaurant in Atlanta, Georgia" --llm_model "gemini-2.5-pro"  # noqa: E501
"""


async def main():
    """Main function for running the application logic in a CLI.
    Takes the prompt, LLM model name, \
        and RAG enabled flag as arguments from the command line.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, required=True)
    parser.add_argument('--llm_model', type=str, required=True)
    parser.add_argument('--rag', action='store_true')
    args = parser.parse_args()
    report.RAG_ENABLED = args.rag
    start = time.perf_counter()
    output_table = await report.create_report(args.prompt, args.llm_model)
    end = time.perf_counter()
    print(f"Total execution time: {end - start:.2f} seconds.")
    print("Final Report Output:\n" + output_table)

if __name__ == "__main__":
    asyncio.run(main())
