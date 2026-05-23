from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MetalPowderState(TypedDict):
    purity_level: float
    particle_size: float
    validation_log: Annotated[List[str], add_messages]

def validate_purity(state: MetalPowderState):
    log = 'Purity validated' if state['purity_level'] >= 99.9 else 'Purity failed'
    return {'validation_log': [log]}

def check_safety_hazards(state: MetalPowderState):
    return {'validation_log': ['Safety hazard check complete']}

def compile_graph():
    graph = StateGraph(MetalPowderState)
    graph.add_node('purity_check', validate_purity)
    graph.add_node('safety_check', check_safety_hazards)
    graph.add_edge('purity_check', 'safety_check')
    graph.add_edge('safety_check', END)
    graph.set_entry_point('purity_check')
    return graph.compile()

graph = compile_graph()
