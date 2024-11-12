import streamlit as st
from conva_ai import ConvaAI

from utils import run_db_query

DEBUG = True

client = ConvaAI(
    assistant_id=st.secrets.conva_assistant_id,
    api_key=st.secrets.conva_api_key,
    assistant_version="6.0.0",
)


def invoke_query_creation(query, history="{}"):
    response = client.invoke_capability_name(
        query=query,
        capability_name="sql_query_generation",
        history=history,
        stream=False,
        timeout=600,
        llm_key="openai-gpt-4o-2024-08-06",
    )

    if DEBUG:
        print("sql_query_creation response: {}\n\n".format(response))

    st.session_state.related = response.related_queries
    st.session_state.history = response.conversation_history
    return response


def invoke_data_analysis(query_response, query, engine):
    exp_query = query_response.parameters.get("timeseries_sql_query", "")
    prc_query = query_response.parameters.get("precise_sql_query", "")

    exp_results = run_db_query(exp_query, engine)
    prc_results = run_db_query(prc_query, engine)

    if DEBUG:
        print(
            "Explanatory Query: {}\nResults: {}\n\nPrecise Query: {}\nResults: {}\n\n".format(
                exp_query, exp_results, prc_query, prc_results
            )
        )

    results_str = "Timeseries Query: {}\nResults: {}SQL Query: {}\nResults: {}".format(
        exp_query, exp_results, prc_query, prc_results
    )

    context = "Analyze this interaction:\nUser Query: {}\n\nDatabase Results: {}".format(
        query,
        results_str,
    )

    context = context.replace("{", "{{").replace("}", "}}")  # noqa

    response = client.invoke_capability_name(
        query=query,
        capability_name="data_analysis",
        capability_context={"data_analysis": context},
        stream=False,
        timeout=600,
    )

    if DEBUG:
        print("data_analysis response: {}\n\n".format(response))
    return response


def invoke_data_visualization(analysis_response, query):
    response = client.invoke_capability_name(
        query=query,
        capability_name="data_visualization",
        capability_context={"data_visualization": analysis_response.message},
        stream=False,
        timeout=600,
    )

    if DEBUG:
        print("data_visualization response: {}\n\n".format(response))

    return response


def invoke_conva_capabilities(query, engine, pb, history="{}"):
    pb.progress(30, "Generating SQL queries...")
    queries_response = invoke_query_creation(query, history)

    pb.progress(50, "Analyzing the responses...")
    analysis_response = invoke_data_analysis(queries_response, query, engine)

    pb.progress(70, "Generating visualizations...")
    graph_response = invoke_data_visualization(analysis_response, query)

    pb.progress(100, "Done")
    return analysis_response, graph_response
