from langgraph.graph import StateGraph
from agents.quiz.agents import quiz_generator_agent
from typing import TypedDict, List, Dict

class QuizState(TypedDict):
    num_questions: int
    questions: List[Dict]

graph = StateGraph(QuizState)

graph.add_node("generate", quiz_generator_agent)

graph.set_entry_point("generate")
graph.set_finish_point("generate")

quiz_graph = graph.compile()
