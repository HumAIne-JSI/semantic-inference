
from dotenv import load_dotenv

from llama_index.llms.openai import OpenAI
from llama_index.core import (
    ServiceContext,
    KnowledgeGraphIndex,
    StorageContext
)
from llama_index.core.retrievers import KnowledgeGraphRAGRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core import Prompt

def get_query_engine(graph_store):
    storage_context = StorageContext.from_defaults(graph_store=graph_store)
    load_dotenv()

    llm = OpenAI(temperature=0, model="gpt-4-0125-preview",)

    graph_rag_retriever = KnowledgeGraphRAGRetriever(
        storage_context=storage_context,
        verbose=False,
        entity_extract_fn=((lambda query : [query])),
    )   



    template = (
    "We have provided context information below. \n"
    "---------------------\n"
    "{context_str}"
    "\n---------------------\n"
    "Given this information, please answer the question: {query_str}\n"
    "And try not to refer to an object using it's id, try to refer to it using it's name that is in a human readable format.\n"
    "And submodels are not independent assets, they are a logical part of an asset, it can be some property of an asset. For instance, \n"
    "a house asset might have a submodel called 'Termal Insulation', this is not a seperate asset, it is something that describes the house asset. Don't mention the 'submodel' concept in your answers because it's an internal one that helps your understanding.\n"
    )

    qa_template = Prompt(template)

    query_engine = RetrieverQueryEngine.from_args(
        graph_rag_retriever,
        text_qa_template=qa_template,
        llm=llm,
        verbose=True,
        graph_traversal_depth=20
    )


    return query_engine

def get_chat_engine(query_engine):
    
    chat_engine = ContextChatEngine.from_defaults(
        query_engine=query_engine,
    )
    return chat_engine