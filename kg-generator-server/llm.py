
import asyncio
from functools import cache
from dotenv import load_dotenv

from llama_index.llms.openai import OpenAI
from llama_index.core import (
    ServiceContext,
    KnowledgeGraphIndex,
    StorageContext
)
from llama_index.core.llms import ChatMessage
from llama_index.core.retrievers import KnowledgeGraphRAGRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core import PromptTemplate
from llama_index.core.response_synthesizers.type import ResponseMode

def get_query_engine(graph_store, llmModel="gpt-4-0125-preview", useQueryGeneration=False, input_string=""):
    storage_context = StorageContext.from_defaults(graph_store=graph_store)
    load_dotenv()
    llm = OpenAI(temperature=0, model="gpt-4-0125-preview",)

    graph_rag_retriever = KnowledgeGraphRAGRetriever(
        storage_context=storage_context,
        verbose=False,
        entity_extract_fn=((lambda query : [query])),
    )   


    sparql_response_coroutine = None
    if (useQueryGeneration):
        sparql_response_coroutine = llm.achat([ChatMessage(role="user", content=f"""
    The SPARQL repository has different prefixes, http://www.entity-with-random-id/ (abbreviated ent) for entities such as machine types, instances of machines, or submodels describing something, 
        http://www.value/ (abbreviated val) for values such as names or numeric values, http://www.entity-with-random-id/ (abbreviated ent) for predicates (unless otherwise specified, sometimes it is http://www.frequent-predicate/ (abbreviated freq)).

    Some of the triples in the repository are (ent:machine_instance_id, freq:is+instance+of, ent:machine_model_id), (ent:machine_model_id, ent:has+name, val:machine_model_name), (ent:machine_instance_id, ent:has+name, val:machine_instance_name), (ent:availability_submodel_id, ent:is+part+of+%2F+describes, ent:machine_instance_id), (ent:availability_submodel_id, ent:has+%22Asset+is+available+for+use%22+value, val:boolean_value), val:boolean_value is one of val:False or val:True, (ent:machine_model_id, ent: (ent:general_type_of_machine_submodel_id, ent:is+part+of+%2F+describes, ent:machine_model_id), (ent:general_type_of_machine_submodel_id, ent:has+name, val:general_type_of_machine_submodel_name), the general_type_of_machine_submodel_name is either "Drilling", "Circle cutting" or "Sawing". In SPARQL query don't use PREFIX ent: ..., instead write whole urls, like for instance <http://www.entity-with-random-id/is+part+of+%2F+describes>.  Note that there are no literals in the SPARQL repo, every value is an URI.
                                        Note that names such as machine_instance_id, machine_model_name, ... are placeholders and not actual values in the repository. Output only the sparql query, no comments. Make sure that the sparql query doesnt return too much, max 20 elements. Its OK to also return values that are related but not exactly what is being asked, for better understanding, e. g. when searching for machine instance names, it also makes sense to search for their model names. Make sure that the (subject, predicate, object) order is as specified!!! Note that it's freq:is+instance+of (expands to http://www.frequent-predicate/is+instance+of)
                                        Write sparql query that helps answer: {input_string}.""")])
    sparql_response = None
    def get_sparql_info(**kwargs):
        nonlocal sparql_response
        print("JOOOOOOOOOo", sparql_response_coroutine, sparql_response)
        if sparql_response_coroutine is None:
            return ""
        if (sparql_response != None):
            return sparql_response
        print("TUUUUUUUUU")
        sparql_query = str(asyncio.run(sparql_response_coroutine).message)
        print(sparql_response)
        try:
            query_results = str(graph_store.query(sparql_query))
            sparql_response = (
            "\n"
            "Additionally, the following sparql query was generated (using your help) and run:"
            "\n---------------------\n"
            f"{sparql_response}"
            "\n---------------------\n"
            "the response of the query is: "
            "\n---------------------\n"
            f"{query_results}"
            "\n---------------------\n"
            "Note that the response was limited to 20 elements, so if there are 20, perhaps there are more but they weren't listed, user should be informed of this. Try to infer from the sparql query what was actually queried. But don't mention the query to the user, you should just process it internally to produce a sensible answer."
            )
        except Exception:
            sparql_response = ""

        print(sparql_response)
        print("GOING OUT")
        return sparql_response

    template = (
    "We have provided context information below. \n"
    "---------------------\n"
    "{context_str}"
    "\n---------------------\n"
    "Given this information, please answer the question: {query_str}\n"
    "And try not to refer to an object using it's id, try to refer to it using it's name that is in a human readable format.\n"
    "And submodels are not independent assets, they are a logical part of an asset, it can be some property of an asset. For instance, \n"
    "a house asset might have a submodel called 'Termal Insulation', this is not a seperate asset, it is something that describes the house asset. Don't mention the 'submodel' concept in your answers because it's an internal one that helps your understanding.\n"
    "{sparql_info}"
    )

    qa_template = PromptTemplate(template, function_mappings={"sparql_info": get_sparql_info})


    # refine_template = None
    # if (useQueryGeneration):
    #     print("TLEEEE")
    #     sparql_response = llm.achat([ChatMessage(role="user", content=f"""
    # The SPARQL repository has different prefixes, http://www.entity-with-random-id/ (abbreviated ent) for entities such as machine types, instances of machines, or submodels describing something, 
    #     http://www.value/ (abbreviated val) for values such as names or numeric values, http://www.entity-with-random-id/ (abbreviated ent) for predicates (unless otherwise specified, sometimes it is http://www.frequent-predicate/ (abbreviated freq)).

    # Some of the triples in the repository are (ent:machine_instance_id, freq:is+instance+of, ent:machine_model_id), (ent:machine_model_id, ent:has+name, val:machine_model_name), (ent:machine_instance_id, ent:has+name, val:machine_instance_name), (ent:availability_submodel_id, ent:is+part+of+%2F+describes, ent:machine_instance_id), (ent:availability_submodel_id, ent:has+%22Asset+is+available+for+use%22+value, val:boolean_value), val:boolean_value is one of val:False or val:True, (ent:machine_model_id, ent: (ent:general_type_of_machine_submodel_id, ent:is+part+of+%2F+describes, ent:machine_model_id), (ent:general_type_of_machine_submodel_id, ent:has+name, val:general_type_of_machine_submodel_name), the general_type_of_machine_submodel_name is either "Drilling", "Circle cutting" or "Sawing". In SPARQL query don't use PREFIX ent: ..., instead write whole urls, like for instance <http://www.entity-with-random-id/is+part+of+%2F+describes>.  Note that there are no literals in the SPARQL repo, every value is an URI.
    #                                     Output only the sparql query, no comments. Make sure that the sparql query doesnt return too much, max 20 elements. Its OK to also return values that are related but not exactly what is being asked, for better understanding. Make sure that the (subject, predicate, object) order is as specified!!! Note that it's freq:is+instance+of (expands to http://www.frequent-predicate/is+instance+of)
    #                                     Write sparql query that helps answer: {input_string}""")])

    query_engine = RetrieverQueryEngine.from_args(   
        graph_rag_retriever,
        text_qa_template=qa_template,
        llm=llm,
        verbose=True,
        graph_traversal_depth=20,
    )


    return query_engine

def get_chat_engine(query_engine):
    
    chat_engine = ContextChatEngine.from_defaults(
        query_engine=query_engine,
    )
    return chat_engine

def query_engine_query(input_string, graph_store, llmModel="gpt-4-0125-preview", useQueryGeneration=False):
    return get_query_engine(graph_store, llmModel, useQueryGeneration, input_string).query(input_string)