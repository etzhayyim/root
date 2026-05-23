from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class ComponentState(TypedDict):
    part_id: str
    specs: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_specs(state: ComponentState) -> dict:
    specs = state.get('specs', {})
    log = []
    if specs.get('load') < 0:
        log.append('Invalid load capacity')
    return {'validation_log': log, 'is_approved': len(log) == 0}

def assembly_workflow(state: ComponentState) -> dict:
    return {'validation_log': ['Assembly logic initialized']}

graph = StateGraph(ComponentState)
graph.add_node('validate', validate_specs)
graph.add_node('assemble', assembly_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)

app = graph.compile()
