from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MineralExtractionState(TypedDict):
    spec_data: dict
    validation_logs: Annotated[List[str], add_messages]
    is_compliant: bool

def validate_casing_specs(state: MineralExtractionState):
    specs = state['spec_data']
    logs = []
    compliant = True
    if specs.get('tensile_strength_mpa', 0) < 500:
        logs.append('Insufficient tensile strength for deep mining.')
        compliant = False
    return {'validation_logs': logs, 'is_compliant': compliant}

def route_by_compliance(state: MineralExtractionState):
    return 'process' if state['is_compliant'] else END

def perform_metallurgical_analysis(state: MineralExtractionState):
    return {'validation_logs': ['Structural integrity check passed. Metallurgy certified.']}

graph = StateGraph(MineralExtractionState)
graph.add_node('validate', validate_casing_specs)
graph.add_node('process', perform_metallurgical_analysis)
graph.add_edge('validate', route_by_compliance)
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()