
from dotenv import load_dotenv

from llama_index.llms.openai import OpenAI
from llama_index.core import (
    ServiceContext,
    KnowledgeGraphIndex,
    StorageContext
)

def get_query_engine(graph_store):
    storage_context = StorageContext.from_defaults(graph_store=graph_store)
    load_dotenv()

    llm = OpenAI(temperature=0, model="gpt-3.5-turbo-instruct")
    service_context = ServiceContext.from_defaults(llm=llm, chunk_size=512)
    index = KnowledgeGraphIndex(
        [],
        storage_context=storage_context,
        service_context=service_context,
        graph_store=graph_store,
        include_embeddings=True
    )

    return index.as_query_engine(
        include_text=True,
        response_mode="tree_summarize",
        embedding_mode="hybrid",
        similarity_top_k=5,
    )