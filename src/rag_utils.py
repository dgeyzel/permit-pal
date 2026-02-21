import asyncio
import time
from conc_workflow import ConcurrentWorkflow
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    get_response_synthesizer
)
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama


def get_context(filenames: [str], prompt: str, llm) -> str:
    """Takes a list of files, and embeds them into a vectorstore.
    An LLM synthesizes a response \
        from the chunks with top similarity to the prompt.
    """
    documents = SimpleDirectoryReader(input_files=filenames).load_data()
    print("Starting document embedding into VectorStoreIndex.")
    start = time.perf_counter()
    ollama_embedding = OllamaEmbedding(
        model_name="embeddinggemma",
        base_url="http://localhost:11434"
    )
    index = VectorStoreIndex.from_documents(
        documents=documents,
        embed_model=ollama_embedding
    )
    end = time.perf_counter()
    print(f"Embed Into VectorStoreIndex Execution Time :  \
        {end - start:.2f} seconds.")
    print("--------------------------------")
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
    print("--------------------------------")
    return str(response)


async def add_context(prompt: str) -> str:
    """Runs the ConcurrentWorkflow to get a list of relevant files.
    Passes the files into get_context \
        to output the generated additional context from the files.
    """
    cwf = ConcurrentWorkflow(
            prompt=prompt,
            timeout=None
        )
    print("--------------------------------")
    print("Starting execution of ConcurrentWorkflow.")
    print("--------------------------------")
    start = time.perf_counter()
    result = await cwf.run()
    end = time.perf_counter()
    print("--------------------------------")
    print(f"Elapsed runtime of ConcurrentWorkflow = \
        {end - start:.2f} seconds.")
    print("--------------------------------")
    print("\nResult of ConcurrentWorkflow\n")
    print("List of relevant files:")
    print("--------------------------------")
    for file in result[0]:
        print(file)
    print("--------------------------------\n")
    print("List of non-relevant files:")
    print("--------------------------------")
    for file in result[1]:
        print(file)
    print("--------------------------------\n")

    if result[0][0] != "No Relevant Results":
        # Run blocking get_context in a thread
        # so the event loop stays responsive.
        additional_context = await asyncio.to_thread(
            get_context,
            result[0],
            prompt,
            get_ollama_llm(),
        )
    else:
        additional_context = " "
    print("RAG loop results:")
    print("--------------------------------")
    print(additional_context)
    print("--------------------------------\n\n")
    return additional_context


def get_ollama_llm(model='phi4-mini'):
    """Helper function that returns an LLM model.
    Called in add_context.
    Passed into get_context. used in get_response_synthesizer.
    """
    ollama_llm = Ollama(
        model=model,
        temperature=0.1,
        max_tokens=200,
        context_window=8000,
        request_timeout=600
    )
    return ollama_llm
