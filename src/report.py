import asyncio
import time
import rag_utils
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Looks at the .env file in the same directory as this python file
# Loads the API key defined in .env as an environment variable
load_dotenv()


# List of LLM models that could be used
LLM_MODEL = [
    'gemini-2.5-pro',
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-3-pro-preview',
    'gemini-3-flash-preview',
    'phi4-mini',
    'qwen2.5:3b-instruct',
    'deepseek-r1:1.5b',
    'llama3.2:3b'
]

# Control whether the RAG loop is used
RAG_ENABLED = False

SYSTEM_PROMPT = """
You are an expert in government rules, codes, and regulations.
As input, you will receive an action that a person wants to accomplish and a location where that action will be performed.
Determine all of licenses, permits, certifications, and other paperwork required to accomplish the action in the location.
Include city, county, state, and federal requirements.  Include insurance requirements.
Include any additional information that is available in CONTEXT.
Structure the answer as a Markdown formatted table and do not return any other output except for the table.
Make sure that the outputted table is formatted in valid Markdown. "|" must be used to seperate table cells, not "||".
Column 1 is the needed permit, document, or action required.
Column 2 is the organization, company, agency, office, bureau, or other entity for which the permit/document is required.
Column 3 is a link to the website for the entity identified in Column 2.
Column 4 is the type of entity in Column 2.  Options are City, County, State, Federal, Private, Other.
Column 5 is a list of requirements, actions, prerequisites, and/or paperwork needed to complete the item in Column 1.
Column 6 is the regulatory source (document, code, statute, rule) that governs the item in Column 1.
Column 7 is a link to the website for the item identified in Column 6.

Here is an example of an input and output:
Input: I want to open a restaurant in Atlanta, Georgia.
Output:
Document/Permit | Agency | Agency Link | Agency Type | Requirements | Regulatory Source | Regulatory Source Link
Zoning Verification |	Atlanta Office of Zoning and Development | https://www.atlantaga.gov/government/departments/city-planning/about-dcp/office-of-zoning-development | City | Verify the property is zoned for a restaurant before signing lease. | |
Register Business | Georgia Secretary of State | https://sos.ga.gov/ | State | Requirements are available at https://sos.ga.gov/how-to-guide/how-guide-register-domestic-entity | Business Services Website | https://sos.ga.gov/corporations-division-georgia-secretary-states-office
Employer Identification Number (EIN) | Internal Revenue Service (IRS) | https://www.irs.gov/businesses | Federal |	Establish a LLC or Corporation first | EIN webform | https://www.irs.gov/businesses/small-businesses-self-employed/get-an-employer-identification-number
State Taxpayer Identification Number (STIN) |	GA Dept of Revenue | https://dor.georgia.gov/ | State | Register the business to collect sales tax. | Georgia Tax Center | https://gtc.dor.ga.gov/_/
Building Permits | Atlanta Office of Buildings | https://www.atlantaga.gov/government/departments/city-planning/about-dcp/office-of-buildings | City | Submit architectural and engineering plans | |
Wastewater Discharge Permit |	Atlanta Department of Watershed Management | https://atlantawatershed.org/ | City | Grease trap sizing & approval. | Food Service Wastewater Discharge Permit Application |
Sign Permit | Atlanta Office of Buildings | https://www.atlantaga.gov/government/departments/city-planning/about-dcp/office-of-buildings | City | Sign Permit Application | |
Food Service Permit |	Fulton County Board of Health | https://fultoncountyboh.com/ | County | Food Service Permit Application, Verification of Residency, Menu, Floor Plans, specification sheets for all kitchen equipment | |
Certified Food Safety Manager | ServSafe | https://www.servsafe.com/ | Private | Complete exam and post certificate at the restaurant | |
City Alcohol License | Atlanta Police Department License and Permits Unit | https://www.atlantapd.org/business/license-and-permits-unit | City | Requirements are here https://www.atlantapd.org/business/alcohol-licenses | |
State Alcohol License | GA Dept of Revenue | https://dor.georgia.gov/ | State | Obtain the City Alcohol License first | |
Certificate of Occupancy |	Atlanta Office of Buildings | https://www.atlantaga.gov/government/departments/city-planning/about-dcp/office-of-buildings | City | Passed all Fire, Health, and Building inspections. | |
Occupational Tax Certificate |	Atlanta Office of Revenue | https://www.atlantaga.gov/government/departments/finance/office-of-revenue | City |	Need Certificate of Occupancy first.  Need New Business Tax Application, SAVE, & E-Verify affidavits. | https://www.atlantaga.gov/government/departments/finance/office-of-revenue/apply-for-a-new-business-occupational-tax-certificate | https://www.atlantaga.gov/government/departments/finance/office-of-revenue/apply-for-a-new-business-occupational-tax-certificate

CONTEXT:
{context}
"""  # noqa: E501


async def gemini_report(input_prompt: str, gemini_model: str) -> str:
    """Sends the input prompt to a Google Gemini LLM model.
    If RAG is enabled, calls add_context from rag_utils to \
        get additional info from the RAG corpus.
    Returns a string that contains the generated report formatted in Markdown.
    """
    additional_context = " "
    if RAG_ENABLED:
        additional_context = await rag_utils.add_context(input_prompt)

    gemini_ai_model = ChatGoogleGenerativeAI(
        model=gemini_model,
        temperature=0.0,  # Gemini 3.0+ defaults to 1.0
        max_tokens=None,
        timeout=None,
        max_retries=2
        )
    messages = [
        ("system", SYSTEM_PROMPT.format(context=additional_context)),
        ("human", input_prompt)
    ]
    print(f"Starting main {gemini_model} model execution.")
    start = time.perf_counter()
    # Run blocking invoke in a thread so the event loop stays responsive
    # (keeps NiceGUI WebSocket alive during long LLM calls).
    ai_msg = await asyncio.to_thread(gemini_ai_model.invoke, messages)
    end = time.perf_counter()
    print(f"Main {gemini_model} model execution time : \
        {end - start:.2f} seconds.")
    output_table = ""
    # Gemini versions 2.5 and 3 have different structures of their outputs
    try:
        output_table = ai_msg.content[0].get('text')
    except AttributeError as e:  # noqa F841
        output_table = str(ai_msg.content)
    return output_table


async def create_report(input_prompt: str, model_name: str) -> str:
    """Wrapper for functions that generate the report.
    Different functions are called to use different LLMs \
        based on the model that is being used.
    """
    output = ""
    if model_name.startswith('gemini'):
        output = await gemini_report(input_prompt, model_name)
    return output
