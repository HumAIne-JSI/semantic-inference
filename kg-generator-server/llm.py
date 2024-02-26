
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
    )

    template = (
    "We have provided context information below. \n"
    "---------------------\n"
    "{context_str}"
    "\n---------------------\n"
    "Given this information, please answer the question and if 'c5nLE3vR' is a substring of some word never display it, e. g. if you see 'a key entity c5nLE3vR4835645539' only write 'a key entity' or something discerning if that is related to key entity like 'a key entity Red' if it has value Red in the answer instead of mentioning c5nLE3vR4835645539: {query_str}\n"
    )
    from llama_index.core import Prompt
    qa_template = Prompt(template)

    return index.as_query_engine(text_qa_template=qa_template)