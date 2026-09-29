import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from modules.graph_engine import process_ablation, process_healing
from modules.perception import load_inference_model, run_ml_pipeline

# 1. Page Configuration (Must be absolutely first)
st.set_page_config(
    page_title="GeoResilience AI | ISRO Route Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODEL CACHING ---
@st.cache_resource
def get_model():
    return load_inference_model()

# This loads the model once when the server starts
unet_model = get_model()

# 2. Initialize Session State
if 'graph_loaded' not in st.session_state:
    st.session_state.graph_loaded = False
if 'ablation_active' not in st.session_state:
    st.session_state.ablation_active = False
if 'selected_coord' not in st.session_state:
    st.session_state.selected_coord = None
if 'healing_active' not in st.session_state:
    st.session_state.healing_active = False

# 3. Sidebar: Control Panel
with st.sidebar:
    st.title("⚙️ Control Panel")
    st.success(f"🧠 Backend: {unet_model['status']} ({unet_model['device']})")
    
    st.markdown("### 1. Perception (Layer 1 & 2)")
    
    if st.button("Run PyTorch Inference"):
        with st.spinner("Processing 0.3m/px satellite raster..."):
            nodes, edges = run_ml_pipeline(unet_model, "data/test_tile.geojson")
            st.session_state.graph_loaded = True
            st.session_state.ablation_active = False
            st.session_state.healing_active = False
            st.session_state.selected_coord = None
        st.success(f"Inference complete. Extracted {nodes} nodes.")
        
    st.markdown("---")
    st.markdown("### 2. Vulnerability (Layer 3)")
    simulate_btn = st.button("Trigger Flood / Ablation", disabled=not st.session_state.graph_loaded)
    if simulate_btn:
        if st.session_state.selected_coord:
            st.session_state.ablation_active = True
            st.session_state.healing_active = False
        else:
            st.warning("Click on the map to select a target node.")

    st.markdown("---")
    st.markdown("### 3. Mitigation (Layer 4)")
    heal_btn = st.button("Deploy Healing Algorithm", disabled=not st.session_state.ablation_active)
    if heal_btn:
        st.session_state.healing_active = True

# 4. Main Canvas
st.title("🌍 GeoResilience AI: Route Resilience Simulator")
st.markdown("Interactive roadmap occlusion and graph-theoretic disaster simulation.")

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Interactive Network Map")
    m = folium.Map(location=[19.0760, 72.8777], zoom_start=12, tiles="OpenStreetMap")
    
    active_nodes = 0
    active_edges = 0
    bypass_count = 0
    
    if st.session_state.graph_loaded:
        try:
            if st.session_state.healing_active and st.session_state.selected_coord:
                healed_geojson, active_nodes, active_edges, bypass_count = process_healing(
                    "data/test_tile.geojson",
                    st.session_state.selected_coord['lat'],
                    st.session_state.selected_coord['lng']
                )
                
                def style_healed(feature):
                    if feature['properties'].get('type') == 'bypass':
                        return {'color': '#FFFF00', 'weight': 5, 'opacity': 1.0, 'dashArray': '5, 5'}
                    else:
                        return {'color': '#0000FF', 'weight': 4, 'opacity': 0.7}
                
                network_layer = folium.GeoJson(healed_geojson, style_function=style_healed).add_to(m)
                m.fit_bounds(network_layer.get_bounds())
                
            # State 2: Fractured Network (Layer 3)
            elif st.session_state.ablation_active and st.session_state.selected_coord:
                fractured_geojson, active_nodes, active_edges, hit_node = process_ablation(
                    "data/test_tile.geojson",
                    st.session_state.selected_coord['lat'],
                    st.session_state.selected_coord['lng']
                )
                
                network_layer = folium.GeoJson(
                    fractured_geojson,
                    style_function=lambda feature: {'color': '#FF0000', 'weight': 4, 'opacity': 0.8}
                ).add_to(m)
                
                # BUG FIX: Only auto-zoom if there are surviving edges to look at
                if active_edges > 0:
                    m.fit_bounds(network_layer.get_bounds())
                
            else:
                with open("data/test_tile.geojson", "r") as f:
                    geojson_data = json.load(f)
                active_edges = len(geojson_data.get("features", []))
                active_nodes = active_edges + 1 # Approximation for display
                
                network_layer = folium.GeoJson(
                    geojson_data,
                    style_function=lambda feature: {'color': '#00FF00', 'weight': 4, 'opacity': 0.8}
                ).add_to(m)
                m.fit_bounds(network_layer.get_bounds())
            
            if st.session_state.selected_coord and not st.session_state.healing_active:
                folium.Marker(
                    location=[st.session_state.selected_coord['lat'], st.session_state.selected_coord['lng']],
                    icon=folium.Icon(color="red", icon="crosshairs", prefix='fa')
                ).add_to(m)
                
        except FileNotFoundError:
            st.error("Graph file not found.")

    st_data = st_folium(m, width=700, height=500)

    if st_data and st_data.get("last_clicked"):
        new_click = st_data["last_clicked"]
        if st.session_state.selected_coord != new_click:
            st.session_state.selected_coord = new_click
            st.session_state.ablation_active = False 
            st.session_state.healing_active = False
            st.rerun()

with col2:
    st.subheader("Resilience Metrics")
    if st.session_state.graph_loaded:
        st.metric(label="Nodes Active", value=str(active_nodes))
        
        if st.session_state.healing_active:
            st.metric(label="Edges Active", value=f"{active_edges} (+{bypass_count} Bypass)")
            st.markdown("---")
            st.success("✅ Network Topology Restored")
        else:
            st.metric(label="Edges Active", value=str(active_edges))
            st.markdown("---")
            if st.session_state.ablation_active:
                st.error("🚨 Network Fractured")
            elif st.session_state.selected_coord:
                st.info("Target acquired. Ready for ablation.")
    else:
        st.info("Run inference to extract graph.")