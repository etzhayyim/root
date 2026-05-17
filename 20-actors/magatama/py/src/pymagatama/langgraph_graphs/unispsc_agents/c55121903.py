from typing import TypedDict
from langgraph.graph import StateGraph, END

class SignSpecs(TypedDict):
    width: float
    height: float
    brightness: int
    ip_rating: str

class GraphState(TypedDict):
    specs: SignSpecs
    is_compliant: bool

def validate_specs(state: GraphState):
    s = state['specs']
    compliant = (s['brightness'] >= 5000) and ('IP65' in s['ip_rating'])
    print(f'Validating specs: {s}. Compliant: {compliant}')
    return {'is_compliant': compliant}

def process_procurement(state: GraphState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(GraphState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()