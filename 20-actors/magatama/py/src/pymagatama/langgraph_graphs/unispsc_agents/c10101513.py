from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PoultryState(TypedDict):
    facility_id: str
    health_status: str
    biosecurity_score: float
    tasks: List[str]

def assess_biosecurity(state: PoultryState):
    score = state.get('biosecurity_score', 0.0)
    status = 'Pass' if score >= 85.0 else 'Flagged_For_Audit'
    return {'health_status': status}

def generate_feed_plan(state: PoultryState):
    return {'tasks': state['tasks'] + ['optimize_nutrient_density']}

def build_graph():
    graph = StateGraph(PoultryState)
    graph.add_node('biosecurity_assessment', assess_biosecurity)
    graph.add_node('feed_optimization', generate_feed_plan)
    graph.add_edge('biosecurity_assessment', 'feed_optimization')
    graph.set_entry_point('biosecurity_assessment')
    graph.add_edge('feed_optimization', END)
    return graph.compile()

graph = build_graph()
