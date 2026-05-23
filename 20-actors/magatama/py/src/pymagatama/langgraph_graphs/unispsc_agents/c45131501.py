from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilmState(TypedDict):
    batch_id: str
    iso_rating: int
    expiry_date: str
    storage_temp_celsius: float
    status: str

def validate_film_specs(state: FilmState):
    if state['iso_rating'] < 25 or state['iso_rating'] > 3200:
        return {'status': 'invalid_iso'}
    return {'status': 'validated'}

def check_storage_logistics(state: FilmState):
    if state['storage_temp_celsius'] > 15:
        return {'status': 'spoiled'}
    return {'status': 'approved'}

graph = StateGraph(FilmState)
graph.add_node('validate', validate_film_specs)
graph.add_node('logistics', check_storage_logistics)
graph.set_entry_point('validate')
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()
