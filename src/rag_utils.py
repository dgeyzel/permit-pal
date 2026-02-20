import time
from dotenv import load_dotenv
from conc_workflow import ConcurrentWorkflow
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    get_response_synthesizer
)
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama

load_dotenv()


def add_context(filenames: [str], prompt: str, llm) -> str:
    documents = SimpleDirectoryReader(input_files=filenames).load_data()
    print("Starting document embedding into VectorStoreIndex.")
    start = time.perf_counter()
    index = VectorStoreIndex.from_documents(
        documents=documents,
        embed_model=HuggingFaceEmbedding(model_name='thenlper/gte-small'),
    )
    end = time.perf_counter()
    print(f"Embed Into VectorStoreIndex Execution Time :  \
        {end - start:.2f} seconds.")
    # Returning 5 chunks that have highest similarity score to the prompt
    # Keeping this number small to lower runtime for the demo
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=5,
    )
    response_synthesizer = get_response_synthesizer(
        response_mode="refine",
        llm=llm
    )
    # Consider changing this to CitationQueryEngine in the future
    # In order to tie chunks back to source document
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
    )
    print("Starting RetrieverQueryEngine execution.")
    start = time.perf_counter()
    response = query_engine.query(prompt)
    end = time.perf_counter()
    print(f"RetrieverQueryEngine execution Time :  \
        {end - start:.2f} seconds.")
    return str(response)


async def get_context(prompt: str) -> str:
    cwf = ConcurrentWorkflow(
            prompt=prompt,
            timeout=None
        )
    print("Starting execution of ConcurrentWorkflow.")
    start = time.perf_counter()
    result = await cwf.run()
    end = time.perf_counter()
    print(f"Result of ConcurrentWorkflow = \n{result}")
    print(f"Elapsed runtime of ConcurrentWorkflow = \
        {end - start:.2f} seconds.")

    if result[0][0] != "No Relevant Results":
        additional_context = add_context(
            result[0],
            prompt,
            get_ollama_llm()
            )
    print(f"RAG loop results:\n {additional_context}")
    return additional_context


def get_ollama_llm(model='phi4-mini'):
    ollama_llm = Ollama(
        model=model,
        temperature=0.1,
        max_tokens=1000,
        context_window=8000,
        request_timeout=600
    )
    return ollama_llm
