# agent_core.py
import os
from typing import TypedDict, List
from io import StringIO
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel

from langgraph.graph import StateGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from tavily import TavilyClient

load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=gemini_key)
tavily = TavilyClient(api_key=tavily_key)

class AgentState(TypedDict):
    task: str
    competitors: List[str]
    csv_file: str
    financial_data: str
    analysis: str
    competitor_data: str
    comparison: str
    feedback: str
    report: str
    content: List[str]
    revision_number: int
    max_revisions: int

class Queries(BaseModel):
    queries: List[str]

# prompts... (reuse yours)
GATHER_FINANCIALS_PROMPT = """You are an expert financial analyst. Gather the financial data for the given company. Provide detailed financial data."""
ANALYZE_DATA_PROMPT = """You are an expert financial analyst. Analyze the provided financial data and provide detailed insights and analysis."""
RESEARCH_COMPETITORS_PROMPT = """You are a researcher tasked with providing information about similar companies for performance comparison. Generate a list of search queries to gather relevant information. Only generate 3 queries max."""
COMPETE_PERFORMANCE_PROMPT = """You are an expert financial analyst. Compare the financial performance of the given company with its competitors based on the provided data.
**MAKE SURE TO INCLUDE THE NAMES OF THE COMPETITORS IN THE COMPARISON.**"""
FEEDBACK_PROMPT = """You are a reviewer. Provide detailed feedback and critique for the provided financial comparison report. Include any additional information or revisions needed."""
WRITE_REPORT_PROMPT = """You are a financial report writer. Write a comprehensive financial report based on the analysis, competitor research, comparison, and feedback provided."""
RESEARCH_CRITIQUE_PROMPT = """You are a researcher tasked with providing information to address the provided critique. Generate a list of search queries to gather relevant information. Only generate 3 queries max."""


def build_graph():
    # nodes: same as yours (no streamlit)
    def gather_financials_node(state: AgentState):
        df = pd.read_csv(StringIO(state["csv_file"]))
        financial_data_str = df.to_string(index=False)
        combined_content = f"{state['task']}\n\nHere is the financial data:\n\n{financial_data_str}"
        messages = [SystemMessage(content=GATHER_FINANCIALS_PROMPT),
                    HumanMessage(content=combined_content)]
        response = model.invoke(messages)
        return {"financial_data": response.content}

    def analyze_data_node(state: AgentState):
        messages = [SystemMessage(content=ANALYZE_DATA_PROMPT),
                    HumanMessage(content=state["financial_data"])]
        response = model.invoke(messages)
        return {"analysis": response.content}

    def research_competitors_node(state: AgentState):
        content = state.get("content", [])
        for competitor in state["competitors"]:
            queries = model.with_structured_output(Queries).invoke([
                SystemMessage(content=RESEARCH_COMPETITORS_PROMPT),
                HumanMessage(content=competitor),
            ])
            for q in queries.queries:
                response = tavily.search(query=q, max_results=2)
                for r in response["results"]:
                    content.append(r["content"])
        return {"content": content}

    def compare_performance_node(state: AgentState):
        content = "\n\n".join(state.get("content", []))
        user_message = HumanMessage(content=f"{state['task']}\n\nHere is the financial analysis:\n\n{state['analysis']}")
        messages = [SystemMessage(content=COMPETE_PERFORMANCE_PROMPT.format(content=content)), user_message]
        response = model.invoke(messages)
        return {"comparison": response.content, "revision_number": state.get("revision_number", 1) + 1}

    def collect_feedback_node(state: AgentState):
        messages = [SystemMessage(content=FEEDBACK_PROMPT),
                    HumanMessage(content=state["comparison"])]
        response = model.invoke(messages)
        return {"feedback": response.content}

    def research_critique_node(state: AgentState):
        feedback = (state.get("feedback") or "").strip()
        if not feedback:
            return {"content": state.get("content", [])}
        queries = model.with_structured_output(Queries).invoke([
            SystemMessage(content=RESEARCH_CRITIQUE_PROMPT),
            HumanMessage(content=feedback),
        ])
        content = state.get("content", [])
        for q in queries.queries:
            response = tavily.search(query=q, max_results=2)
            for r in response["results"]:
                content.append(r["content"])
        return {"content": content}

    def write_report_node(state: AgentState):
        messages = [SystemMessage(content=WRITE_REPORT_PROMPT),
                    HumanMessage(content=state["comparison"])]
        response = model.invoke(messages)
        return {"report": response.content}

    def should_continue(state: AgentState):
        return "write_report" if state["revision_number"] > state["max_revisions"] else "collect_feedback"

    builder = StateGraph(AgentState)
    builder.add_node("gather_financials", gather_financials_node)
    builder.add_node("analyze_data", analyze_data_node)
    builder.add_node("research_competitors", research_competitors_node)
    builder.add_node("compare_performance", compare_performance_node)
    builder.add_node("collect_feedback", collect_feedback_node)
    builder.add_node("research_critique", research_critique_node)
    builder.add_node("write_report", write_report_node)

    builder.set_entry_point("gather_financials")
    builder.add_edge("gather_financials", "analyze_data")
    builder.add_edge("analyze_data", "research_competitors")
    builder.add_edge("research_competitors", "compare_performance")
    builder.add_edge("collect_feedback", "research_critique")
    builder.add_edge("research_critique", "compare_performance")

    builder.add_conditional_edges(
        "compare_performance",
        should_continue,
        {"write_report": "write_report", "collect_feedback": "collect_feedback"},
    )

    return builder.compile()

graph = build_graph()

def run_analysis(task: str, competitors: list[str], csv_text: str, max_revisions: int) -> str:
    initial_state = {
        "task": task,
        "competitors": competitors,
        "csv_file": csv_text,
        "max_revisions": max_revisions,
        "revision_number": 1,
        "content": [],
        "financial_data": "",
        "analysis": "",
        "competitor_data": "",
        "comparison": "",
        "feedback": "",
        "report": "",
    }
    final = None
    for update in graph.stream(initial_state):
        final = update
    # final is a dict like {"write_report": {"report": "..."} } depending on stream mode
    # simplest: search for report value
    if isinstance(final, dict):
        for _, v in final.items():
            if isinstance(v, dict) and "report" in v:
                return v["report"]
    raise RuntimeError("No report produced")