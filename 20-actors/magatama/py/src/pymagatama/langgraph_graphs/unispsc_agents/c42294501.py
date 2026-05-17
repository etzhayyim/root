from typing import TypedDict
from langgraph.graph import StateGraph, END

class OphthalmicState(TypedDict):
    sterilization_cert: bool
    biocompatibility_check: bool
    approved: bool

def validate_specs(state: OphthalmicState) -> OphthalmicState:
    state['approved'] = state['sterilization_cert'] and state['biocompatibility_check']
    return state

graph = StateGraph(OphthalmicState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

# Compile the graph
app = graph.compile()