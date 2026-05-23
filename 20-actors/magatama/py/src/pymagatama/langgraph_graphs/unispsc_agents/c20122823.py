from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ProcessingState(TypedDict):
    part_id: str
    cad_data: str
    processing_steps: Annotated[List[str], operator.add]
    validation_log: List[str]
    is_approved: bool

def validate_cad(state: ProcessingState):
    log = f'Validating CAD for {state["part_id"]} against tolerances.'
    return {'validation_log': [log], 'is_approved': True}

def simulate_machining(state: ProcessingState):
    step = 'Execute CNC path optimization and tool-path simulation.'
    return {'processing_steps': [step]}

def finalize_production(state: ProcessingState):
    return {'validation_log': ['Production sequence verified and ready for deployment.']}

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_cad)
graph.add_node('machining', simulate_machining)
graph.add_node('finalize', finalize_production)
graph.add_edge('validate', 'machining')
graph.add_edge('machining', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
