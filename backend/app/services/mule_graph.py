import networkx as nx

G = nx.DiGraph()

def update_graph(src: str, dst: str, amount: float):
    G.add_node(src)
    G.add_node(dst)
    G.add_edge(src, dst, amount=amount)

def mule_risk(iban: str) -> int:
    fan_in = G.in_degree(iban)
    fan_out = G.out_degree(iban)
    if fan_in >= 5 and fan_out >= 5:
        return 85
    if fan_in >= 3 and fan_out >= 1:
        return 60
    return 20
