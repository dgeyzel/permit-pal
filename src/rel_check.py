import pathlib
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Looks at the .env file in the same directory as this python file
# Loads the API key defined in .env as an environment variable
load_dotenv()


async def rel_check(prompt: str, file_name: str) -> dict[str, str]:
    MODEL = []
    MODEL.append("gemini-3-flash-preview")
    SYSTEM_PROMPT = """
    You are an expert in government rules, codes, and regulations.  You will be given two inputs:
    1 - A document to examine.  This is the CONTEXT.
    2 - An action or desired outcome and a location where that action or outcome will occur.  This is the USER action/outcome.

    You must determine whether the document is relevant to the action/outcome and the location information provided.
    The document will have information on rules, regulations, laws, codes, processes, licenses, permits, certifications, and other paperwork.
    To be relevant, the document must contain information that can help someone take the specified action or accomplish the specified goal.
    The document must also apply to the location specified.
    The document is not relevant if it is meant for a different city, county, state, or country than the specified location.

    Examples:
    1 - If the desired outcome is to open a restaurant in Atlanta, Georgia,
    then a document from the county of Fulton County about Food Service Permits is relevant.
    2 - If the desired outcome is to open a restaurant in Atlanta, Georgia,
    then a document from the city of San Diego about Food Service Permits is not relevant.
    3 - If the desired outcome is to become a barber in Butte, Montana,
    then a document about forestry is not relevant.

    If the document is relevant to the action and location, return the answer only as “Yes” without the quotes.
    Do not include any other output except “Yes”.
    If the document is not relevant to the action and location, return the answer only as “No” without the quotes.
    Do not include any other output except “No”.

    USER:
    {action}

    """  # noqa: E501
    filepath = pathlib.Path(file_name)
    client = genai.Client()
    response = await client.aio.models.generate_content(
      model=MODEL[0],
      contents=[
        types.Part.from_bytes(
            data=filepath.read_bytes(),
            mime_type='application/pdf',
        ),
        SYSTEM_PROMPT.format(action=prompt)
      ]
    )
    return {file_name: response.text}
