import re
import tiktoken
from sqlalchemy import text


def num_tokens_from_string(string: str, model_name: str) -> int:
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(string))
    print("num tokens = {}".format(num_tokens))
    return num_tokens


def escape_braces(text: str) -> str:
    text = re.sub(r"(?<!\{)\{(?!\{)", r"{{", text)  # noqa
    text = re.sub(r"(?<!\})\}(?!\})", r"}}", text)  # noqa
    return text


def maybe_trim_context(context: str) -> str:
    length = len(context)
    tokens = num_tokens_from_string(context, "gpt-4o-mini")
    start = 0
    finish = length
    while tokens > 120 * 1000:
        finish = int(finish - 0.1 * finish)
        context = context[start:finish]
        tokens = num_tokens_from_string(context, "gpt-4o-mini")
    return context


def get_md_normal_text(text):
    return "<p> {} </p>".format(text)


def get_md_hyperlink(text):
    return "<a href={}>{}</a>".format(text, text)


def get_md_list(arr):
    lis = ""
    for elem in arr:
        if "$" in elem:
            elem = elem.replace("$", "\\$")
        lis += "<li> {} </li>".format(elem)
    return "<list> {} </list>".format(lis)


def preprocess_query(query):
    query = query.lower()
    if "bangalore" in query:
        query = query.replace("bangalore", "bengaluru")
    pattern = r"(state_name\s+like\s+')%([\w\s]+)%'"
    replacement = lambda m: f"{m.group(1)}%{'-'.join(m.group(2).split())}%'"
    query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
    return query


def run_db_query(query: str, engine) -> list:
    try:
        if not query:
            return []

        query = preprocess_query(query)
        with engine.connect() as connection:
            result = connection.execute(text(query))
            rows = result.fetchall()
            return [row._mapping for row in rows]  # noqa
    except (Exception,) as e:
        print("Error running query: {}".format(e))
        return []
