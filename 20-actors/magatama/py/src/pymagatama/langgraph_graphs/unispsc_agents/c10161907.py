from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SwineState(TypedDict):
    farm_id: str
    health_metrics: dict
    compliance_score: float
    process_steps: List[str]

def validate_biosecurity(state: SwineState) -> SwineState:
    state['process_steps'].append('BIODEFENSE_CHECK')
    state['compliance_score'] = 0.95 if state['health_metrics'].get('clean') else 0.5
    return state

def run_production_analysis(state: SwineState) -> SwineState:
    state['process_steps'].append('PRODUCTION_ANALYSIS')
    return state

graph = StateGraph(SwineState)
graph.add_node('biosecurity', validate_biosecurity)
graph.add_node('production', run_production_analysis)
graph.add_edge('biosecurity', 'production')
graph.add_edge('production', END)
graph.set_entry_point('biosecurity')
graph = graph.compile()