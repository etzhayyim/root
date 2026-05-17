from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class LivestockState(TypedDict):
    animal_id: str
    quarantine_passed: bool
    health_certified: bool
    steps: List[str]

def validate_health_docs(state: LivestockState):
    print(f'Validating health docs for {state['animal_id']}')
    return {'health_certified': True, 'steps': state['steps'] + ['docs_verified']}

def perform_quarantine(state: LivestockState):
    print(f'Performing quarantine for {state['animal_id']}')
    return {'quarantine_passed': True, 'steps': state['steps'] + ['quarantine_complete']}

def create_livestock_graph():
    graph = StateGraph(LivestockState)
    graph.add_node('verify_docs', validate_health_docs)
    graph.add_node('quarantine', perform_quarantine)
    graph.set_entry_point('verify_docs')
    graph.add_edge('verify_docs', 'quarantine')
    graph.add_edge('quarantine', END)
    return graph.compile()