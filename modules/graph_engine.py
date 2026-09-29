import json
import math
import networkx as nx
from itertools import combinations

def _load_graph(geojson_path):
    with open(geojson_path, "r") as f:
        data = json.load(f)
        
    G = nx.Graph()
    for feature in data["features"]:
        u = feature["properties"]["u"]
        v = feature["properties"]["v"]
        coords = feature["geometry"]["coordinates"]
        G.add_node(u, pos=(coords[0][0], coords[0][1]))
        G.add_node(v, pos=(coords[1][0], coords[1][1]))
        G.add_edge(u, v)
    return G

def process_ablation(geojson_path, target_lat, target_lon):
    G = _load_graph(geojson_path)
            
    nearest_node = None
    min_dist = float('inf')
    for node, attr in G.nodes(data=True):
        n_lon, n_lat = attr['pos']
        dist = math.hypot(n_lon - target_lon, n_lat - target_lat)
        if dist < min_dist:
            min_dist = dist
            nearest_node = node
            
    if nearest_node in G:
        G.remove_node(nearest_node)
        
    fractured_features = []
    for u, v in G.edges():
        pos_u = G.nodes[u]['pos']
        pos_v = G.nodes[v]['pos']
        fractured_features.append({
            "type": "Feature",
            "properties": {"type": "original"},
            "geometry": {"type": "LineString", "coordinates": [pos_u, pos_v]}
        })
        
    fractured_geojson = {
        "type": "FeatureCollection",
        "features": fractured_features
    }
    
    return fractured_geojson, len(G.nodes()), len(G.edges()), nearest_node

def process_healing(geojson_path, target_lat, target_lon):
    G = _load_graph(geojson_path)
    
    nearest_node = None
    min_dist = float('inf')
    for node, attr in G.nodes(data=True):
        n_lon, n_lat = attr['pos']
        dist = math.hypot(n_lon - target_lon, n_lat - target_lat)
        if dist < min_dist:
            min_dist = dist
            nearest_node = node
            
    if nearest_node in G:
        G.remove_node(nearest_node)
        
    components = list(nx.connected_components(G))
    bypass_edges_count = 0
    
    if len(components) > 1:
        main_island = components[0]
        
        for i in range(1, len(components)):
            island = components[i]
            
            best_bridge = None
            min_bridge_dist = float('inf')
            
            for u in main_island:
                for v in island:
                    pos_u = G.nodes[u]['pos']
                    pos_v = G.nodes[v]['pos']
                    dist = math.hypot(pos_u[0] - pos_v[0], pos_u[1] - pos_v[1])
                    if dist < min_bridge_dist:
                        min_bridge_dist = dist
                        best_bridge = (u, v)
                        
            if best_bridge:
                G.add_edge(best_bridge[0], best_bridge[1], type="bypass")
                bypass_edges_count += 1
                main_island = main_island.union(island)

    healed_features = []
    for u, v, data in G.edges(data=True):
        pos_u = G.nodes[u]['pos']
        pos_v = G.nodes[v]['pos']
        edge_type = data.get("type", "original")
        
        healed_features.append({
            "type": "Feature",
            "properties": {"type": edge_type},
            "geometry": {"type": "LineString", "coordinates": [pos_u, pos_v]}
        })
        
    healed_geojson = {
        "type": "FeatureCollection",
        "features": healed_features
    }
    
    return healed_geojson, len(G.nodes()), len(G.edges()), bypass_edges_count