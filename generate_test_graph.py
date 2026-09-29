import networkx as nx
import json

def create_vulnerable_geojson():
    # West Zone (2x2 grid)
    G1 = nx.grid_2d_graph(2, 2)
    # East Zone (2x2 grid shifted east)
    G2 = nx.grid_2d_graph(2, 2)
    G2 = nx.relabel_nodes(G2, {n: (n[0]+3, n[1]) for n in G2.nodes()})
    
    G = nx.compose(G1, G2)
    
    # The Critical Bridge Node
    bridge_node = (2, 0)
    G.add_node(bridge_node)
    
    # Connect West Zone to Bridge, and Bridge to East Zone
    G.add_edge((1, 0), bridge_node)
    G.add_edge(bridge_node, (3, 0))
    
    base_lat = 19.0760
    base_lon = 72.8777
    offset = 0.005

    features = []
    pos = {}
    for node in G.nodes():
        x, y = node
        lon = base_lon + (x * offset)
        lat = base_lat + (y * offset)
        pos[node] = (lon, lat)
        
    for u, v in G.edges():
        feature = {
            "type": "Feature",
            "properties": {"u": str(u), "v": str(v), "weight": 1.0},
            "geometry": {"type": "LineString", "coordinates": [pos[u], pos[v]]}
        }
        features.append(feature)
        
    with open("data/test_tile.geojson", "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f)
        
    print("Vulnerable graph saved to data/test_tile.geojson")

if __name__ == "__main__":
    create_vulnerable_geojson()