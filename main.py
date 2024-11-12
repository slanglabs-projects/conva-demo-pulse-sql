import json
import os

import random
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

import pandas as pd
from sqlalchemy import create_engine

from conva import invoke_conva_capabilities

# Read CSV into a pandas DataFrame
tpath = "data/pp_transactions.csv"
upath = "data/pp_users.csv"

tdf = pd.read_csv(tpath)
udf = pd.read_csv(upath)

engine = create_engine("sqlite:///:memory:")

tdf.to_sql("phonepe_transactions_data", con=engine, index=False, if_exists="replace")
udf.to_sql("phonepe_users_data", con=engine, index=False, if_exists="replace")

DEBUG = False

if not "sources" in st.session_state:
    st.session_state.sources = []

if not "history" in st.session_state:
    st.session_state.history = "{}"

if not "related" in st.session_state:
    st.session_state.related = []

if not "new_query" in st.session_state:
    st.session_state.new_query = None

if not "started" in st.session_state:
    st.session_state.started = False

if os.path.exists("data/related.json"):
    with open("data/related.json", "r") as f:
        st.session_state.related = json.load(f)


def get_bot_response(user_input, pb):
    pb.progress(100, "Done")

    summary_response, graph_response = invoke_conva_capabilities(user_input, engine, pb, st.session_state.history)

    summary = summary_response.message

    graph_data = {
        "description": graph_response.parameters.get("description"),
        "structure": graph_response.parameters.get("structure"),
        "data": graph_response.parameters.get("data"),
    }
    return summary, graph_data


def output2df(output):
    return pd.DataFrame(output["data"])


def suggest_visualizations(df, _description):
    """
    Suggest appropriate visualizations based on the dataframe structure.
    """
    num_columns = df.select_dtypes(include=["int64", "float64"]).columns
    cat_columns = df.select_dtypes(include=["object", "category"]).columns

    suggestions = []

    if len(num_columns) >= 1 and len(cat_columns) >= 1:
        suggestions.append(("Bar Chart", cat_columns[0], num_columns[0]))

    return suggestions


def create_visualization(df, chart_type, x_column, y_column):
    """
    Create a Plotly visualization based on the selected chart type and columns.
    """
    if chart_type == "Bar Chart":
        fig = px.bar(df, x=x_column, y=y_column)
    elif chart_type == "Scatter Plot":
        fig = px.scatter(df, x=x_column, y=y_column)
    elif chart_type == "Line Chart":
        fig = px.line(df, x=x_column, y=y_column)
    elif chart_type == "Histogram":
        fig = px.histogram(df, x=x_column)
    elif chart_type == "Box Plot":
        fig = px.box(df, x=x_column, y=y_column)
    elif chart_type == "Pie Chart":
        fig = px.bar(df, x=x_column, y=y_column)
    else:
        fig = go.Figure()

    return fig


def generate_graph(data):
    df = output2df(data)
    print(df)
    suggestions = suggest_visualizations(df, data.get("description", ""))
    if suggestions:
        # select a random suggestion
        chart_type, x_column, y_column = random.choice(suggestions)
        fig = create_visualization(df, chart_type, x_column, y_column)
    else:
        fig = go.Figure()

    return fig


st.markdown(
    """
<style>
button * {
    height: auto;
}
button p {
    font-size: .8em;
}
</style>
""",
    unsafe_allow_html=True,
)


def handle_button_click(query):
    st.session_state.new_query = query
    if not st.session_state.started:
        st.session_state.started = True


def process_query(prompt):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        placeholder = st.empty()
        _, col1, _ = placeholder.columns([1, 3, 1])
        pb = col1.progress(0, "Understanding your query...")

        # Get bot response (text and graph data)
        response, graph_data = get_bot_response(prompt, pb)

        if not response:
            response = "Sorry, I couldn't find any information on that."

        placeholder.empty()

        st.markdown(response)
        if graph_data.get("data"):
            fig = generate_graph(graph_data)
            st.plotly_chart(fig, use_container_width=True)

    # Add assistant response to chat history
    if graph_data.get("data"):
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
                "graph": fig,
            }
        )
    else:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
            }
        )

    if st.session_state.related:
        related = sorted(st.session_state.related, key=lambda l: len(l))
        col1, col2, col3 = st.columns(3)
        l = len(related)
        if l > 0:
            col1.button(related[0], key="{}_1".format(related[0]), on_click=handle_button_click, args=[related[0]])
        if l > 1:
            col2.button(related[1], key="{}_2".format(related[1]), on_click=handle_button_click, args=[related[1]])
        if l > 2:
            col3.button(related[2], key="{}_3".format(related[2]), on_click=handle_button_click, args=[related[2]])


def main():
    st.title("PhonePe Pulse Q&A")
    st.divider()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "graph" in message:
                st.plotly_chart(message["graph"], use_container_width=True)
            if "sources" in message:
                sources = message["sources"]
                with st.expander("Sources"):
                    for index, url in enumerate(sources.keys()):
                        st.markdown(
                            "{}. <a href='{}'>{}</a>".format(index + 1, url, url),
                            unsafe_allow_html=True,
                        )

    if not st.session_state.started:
        if st.session_state.related:
            related = sorted(st.session_state.related, key=lambda l: len(l))
            col1, col2, col3 = st.columns(3)
            l = len(related)
            if l > 0:
                col1.button(related[0], on_click=handle_button_click, args=[related[0]])
            if l > 1:
                col2.button(related[1], on_click=handle_button_click, args=[related[1]])
            if l > 2:
                col3.button(related[2], on_click=handle_button_click, args=[related[2]])

    if st.session_state.new_query:
        prompt = st.session_state.new_query
        st.session_state.new_query = None
        process_query(prompt)

    # React to user input
    if prompt := st.chat_input("What would you like to know?"):
        if not st.session_state.started:
            st.session_state.started = True
        process_query(prompt)


if __name__ == "__main__":
    main()
