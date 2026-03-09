import streamlit as st
import plotly.graph_objects as go
from core.geometry import GeometryEngine
import streamlit as st
import streamlit.components.v1 as components

# --- Page Configuration ---
st.set_page_config(
    page_title="Solar Structural Designer",
    page_icon="☀️",
    layout="wide"
)

def main():
    st.title("☀️ Solar Structure Generator")
    st.markdown("Build, Visualize, and Analyze Solar Mounting Structures")

    # ==========================================
    # 1. SIDEBAR - INPUT PARAMETERS
    # ==========================================
    with st.sidebar:
        st.header("⚙️ Design Parameters")
        
        # --- Section: Panel Dimensions ---
        with st.expander("Panel Dimensions", expanded=True):
            p_len = st.number_input("Length (m)", 0.5, 3.0, 1.7)
            p_wid = st.number_input("Width (m)", 0.5, 2.0, 1.0)
            p_thk = st.number_input("Thickness (m)", 0.01, 0.1, 0.04)

        # --- Section: Array Config ---
        with st.expander("Array Configuration", expanded=True):
            angle = st.slider("Tilt Angle (°)", 0, 60, 30)
            c1, c2 = st.columns(2)
            rows = c1.number_input("Rows", 1, 50, 2)
            cols = c2.number_input("Columns", 1, 50, 3)
            
            st.caption("Support Columns Layout")
            c3, c4 = st.columns(2)
            x_cols = c3.number_input("Cols (X-axis)", 1, 10, 2, help="Number of support columns along width")
            y_cols = c4.number_input("Cols (Y-axis)", 1, 10, 2, help="Number of support columns along depth")

        # --- Section: Structure Details ---
        with st.expander("Structure Profile"):
            col_min_h = st.number_input("Min Height (m)", 0.5, 5.0, 2.0)

        # --- Section: Offsets & Gaps ---
        with st.expander("Offsets & Spacing (m)"):
            h_gap = st.number_input("Panel H-Gap", 0.0, 0.1, 0.02)
            v_gap = st.number_input("Panel V-Gap", 0.0, 0.1, 0.02)
            st.markdown("---")
            front_off = st.number_input("Front Column Offset", 0.0, 2.0, 0.6)
            rear_off = st.number_input("Rear Column Offset", 0.0, 2.0, 0.8)
            purlin_off = st.number_input("Purlin Offset", 0.0, 1.0, 0.3)
            rafter_purlin_off = st.number_input("Rafter-Purlin Offset", 0.0, 2.0, 0.4)
            hor_panel_off = st.number_input("Horizontal Panel Overhang", 0.0, 2.0, 0.6)
            #hor_purlin_off = st.number_input("Horizontal Purlin Overhang", 0.0, 2.0, 0.2)

        # --- Section: Structure Details ---
        with st.expander("Solar Farm Details"):
            copies_in_x = st.number_input("Duplicates in X", 1, 10, 1)
            x_gap = st.number_input("Gap in X (m)" , 0.0, 50.0, 20.0)
            copies_in_y = st.number_input("Duplicates in Y", 1, 10, 1)
            y_gap = st.number_input("Gap in Y (m)", 0.0, 50.0, 20.0)

        with st.expander("RCC Block Details"):
            b_len, b_wid, b_high = st.columns(3)
            blk_len = b_len.number_input("Block Length (m)", 0.5, 5.0, 1.0)
            blk_wid = b_wid.number_input("Block Width (m)", 0.5, 5.0, 1.0)
            blk_heigth = b_high.number_input("Block Height (m)", 0.5, 5.0, 1.0)

        with st.expander("Section Profiles"):
            
            st.subheader("Column Cross Section (mm)")
            c_len, c_wid, c_thk, c_mesh = st.columns(4)
            col_len = c_len.number_input("Column Length", 20, 250, 150)
            col_wid = c_wid.number_input("Column Width", 5, 100, 40)
            col_thk = c_thk.number_input("Column Thickness", 0.01, 8.0, 2.0)
            col_mesh = c_mesh.number_input("Column Mesh Size", 0.005, 0.01, 0.008)


            st.subheader("Rafter Cross Section (mm)")
            r_len, r_wid, r_thk, r_mesh = st.columns(4)
            raf_len = r_len.number_input("Rafter Length", 20, 250, 150)
            raf_wid = r_wid.number_input("Rafter Width", 5, 100, 40)
            raf_thk = r_thk.number_input("Rafter Thickness", 0.01, 8.0, 2.0)
            raf_mesh = r_mesh.number_input("Rafter Mesh Size", 0.005, 0.01, 0.008)

            st.subheader("Purlin Cross Section (mm)")
            pr_len, pr_wid, pr_thk, p_mesh = st.columns(4)
            pur_len = pr_len.number_input("Purlin Length", 20, 250, 150)
            pur_wid = pr_wid.number_input("Purlin Width", 5, 100, 40)
            pur_thk = pr_thk.number_input("Purlin Thickness", 0.01, 8.0, 2.0)
            pur_mesh = p_mesh.number_input("Purlin Mesh Size", 0.005, 0.01, 0.008)

        ############################# WIND LOAD ##########################################

        st.header("Wind Load")

        with st.expander("Wind Load Perimeters", expanded=True):
            # --- Input Section ---
            # User's starting code for Velocity (B3 in the formula)
            # Note: The formula constant 0.613 requires velocity in m/s (mps). 
            # We take input in km/h as requested and will convert it.
            velocity_kmh = st.number_input("Wind Speed (km/h)", min_value=20, max_value=200, value=30)
            
            # Inputs mapped from the PDF "Inputs" table  required for the formula:
            
            # B5: Topographical Factor (Kzt) - Default 0.85 from PDF
            kzt = st.number_input("Topographical Factor (Kzt)", value=0.85)
            
            # B6: Directionality Factor (Kd) - Default 1 from PDF
            kd = st.number_input("Directionality Factor (Kd)", value=1.0)
            
            # B10: Velocity Pressure Coeff at height z (Kz) - Default 0.76 from PDF
            kz = st.number_input("Velocity Pressure Coeff (Kz)", value=0.76)
            
            # B11: Ground Elevation Factor (Ke) - Default 1 from PDF
            ke = st.number_input("Ground Elevation Factor (Ke)", value=1.0)

            # --- Calculation Section ---
            # Convert km/h to m/s (mps) for the formula
            velocity_mps = velocity_kmh / 3.6 
            
            # Formula: =0.613 * B11 * B10 * B5 * B6 * (B3^2)
            # Mapping: B11=Ke, B10=Kz, B5=Kzt, B6=Kd, B3=Velocity_mps
            velocity_pressure = 0.613 * ke * kz * kzt * kd * (velocity_mps ** 2)

            st.markdown("---")
            st.write(f"**Velocity Pressure (qz):** {velocity_pressure:.2f} N/m²")


    # ==========================================
    # 2. LOGIC - PACK DATA & GENERATE
    # ==========================================
    
    # Pack inputs into a clean dictionary to pass to the core logic
    params = {
        'panel_length': p_len, 'panel_width': p_wid, 'panel_thickness': p_thk,
        'angle': angle, 'rows': rows, 'cols': cols,
        'x_cols': x_cols, 'y_cols': y_cols,
        'col_min_height': col_min_h, 
        'h_gap': h_gap, 'v_gap': v_gap,
        'front_offset': front_off, 'rear_offset': rear_off, 'purlin_offset': purlin_off, 'rafter_purlin_offset': rafter_purlin_off, 'hor_panel_overhang': hor_panel_off, #'hor_purlin_overhang': hor_purlin_off,
        'col_len': col_len, 'col_wid': col_wid, 'col_thk': col_thk, "col_mesh": col_mesh,
        'raf_len': raf_len, 'raf_wid': raf_wid, 'raf_thk': raf_thk, "raf_mesh": raf_mesh,
        'pur_len': pur_len, 'pur_wid': pur_wid, 'pur_thk': pur_thk, "pur_mesh": pur_mesh,
        'copies_in_x': copies_in_x, 'copies_in_y': copies_in_y, 'x_gap': x_gap, 'y_gap': y_gap,
        'blk_len': blk_len, 'blk_wid': blk_wid, 'blk_heigth': blk_heigth,
        'velocity_pressure': velocity_pressure
    }

    # Call the Engine
    # try:
    #     geometry_meshes, fea_nodes = GeometryEngine.generate_structure(params)
    # except Exception as e:
    #     st.exception(f"Error generating geometry: {e}")
    #     st.stop()

    geometry_meshes, fea_nodes, fea_members, model = GeometryEngine.generate_structure(params)

    # print("Geometry Meshes: ", geometry_meshes)
    # print("FEA Nodes: ", fea_nodes)
    # print("FEA Members: ", fea_members)


    # ==========================================
    # 3. VISUALIZATION - PLOTLY 3D
    # ==========================================
    tab1, tab2, tab3, tab4 = st.tabs(["🏗️ Solid CAD Model", "🔴 FEA Nodal Model", "📐 Member Wireframe", "💻 PyNite FEA Results"])
    # --- TAB 1: EXISTING CAD MODEL ---
    with tab1:
        fig_cad = go.Figure(data=geometry_meshes)
        fig_cad.update_layout(
            scene=dict(
                aspectmode='data',
                xaxis=dict(title="X (Width)", backgroundcolor="rgb(240, 240, 240)"),
                yaxis=dict(title="Y (Depth)", backgroundcolor="rgb(240, 240, 240)"),
                zaxis=dict(title="Z (Height)", backgroundcolor="rgb(230, 230, 250)"),
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
            ),
            margin=dict(l=0, r=0, b=0, t=0),
            height=700,
        )
        st.plotly_chart(fig_cad, use_container_width=True)

        # ==========================================
        # 4. SUMMARY METRICS
        # ==========================================
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Panels", rows * cols)
        c2.metric("System Area", f"{(rows * cols * p_len * p_wid):.2f} m²")
        # A placeholder for future steps
        c3.button("Calculate Wind Loads ➔", help="Feature coming in Step 3")

    # --- TAB 2: NEW NODAL MODEL ---
    with tab2:
        if fea_nodes:
            # Unpack the nodes into X, Y, Z lists for Plotly
            x_vals = [p[0] for p in fea_nodes]
            y_vals = [p[1] for p in fea_nodes]
            z_vals = [p[2] for p in fea_nodes]

            # Create a Scatter3d plot specifically for nodes
            fig_nodes = go.Figure(data=[go.Scatter3d(
                x=x_vals, y=y_vals, z=z_vals,
                mode='markers',
                marker=dict(size=5, color='red', symbol='circle', line=dict(width=1, color='black')),
                name="Nodes"
            )])

            fig_nodes.update_layout(
                scene=dict(
                    aspectmode='data', # Keeps the 1:1:1 spatial ratio
                    xaxis=dict(title="X (Width)"),
                    yaxis=dict(title="Y (Depth)"),
                    zaxis=dict(title="Z (Height)"),
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
                ),
                margin=dict(l=0, r=0, b=0, t=0),
                height=700,
            )
            st.plotly_chart(fig_nodes, use_container_width=True)
        else:
            st.info("Add coordinate points to your 'fea_nodes' list in the backend to see them here!")

# --- TAB 3: MEMBER WIREFRAME ---
    with tab3:

        if fea_members:
            x_coords = fea_members[0] if len(fea_members) > 0 else []
            y_coords = fea_members[1] if len(fea_members) > 1 else []
            z_coords = fea_members[2] if len(fea_members) > 2 else []

            fig_members = go.Figure() # defining the figure outside the loop to add multiple traces for each member
                
            # Loop through members and insert 'None' to break the continuous line
            for i in range(len(x_coords)):
                x_cords = x_coords[i]
                y_cords = y_coords[i]
                z_cords = z_coords[i]
                
                # Create the line plot
                fig_members.add_trace(go.Scatter3d(
                    x=x_cords, 
                    y=y_cords, 
                    z=z_cords,
                    mode='lines',
                    line=dict(color='blue', width=3),
                    name="Structural Members"
                ))

                print(f"Member {i+1}: X={x_cords}, Y={y_cords}, Z={z_cords}")

            fig_members.update_layout(
                scene=dict(
                    aspectmode='data',
                    xaxis=dict(title="X (Width)"),
                    yaxis=dict(title="Y (Depth)"),
                    zaxis=dict(title="Z (Height)"),
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
                ),
                margin=dict(l=0, r=0, b=0, t=0),
                height=700,
            )
            st.plotly_chart(fig_members, use_container_width=True)


    from Pynite.Rendering import Renderer

    # ... inside your Streamlit app ...
    with tab4: # Assuming this is your new tab
        
        # 1. Initialize the PyNite Renderer
        rndr = Renderer(model)
        rndr.annotation_size = 0.2
        rndr.deformed_shape = True
        rndr.deformed_scale = 200
        rndr.render_nodes = True
        rndr.render_loads = True
        rndr.labels = False
        rndr.color_map = "dz"
        
        # 2. Setup the plotter but DO NOT call rndr.render_model()
        # render_model() hardcodes plotter.show(), which we want to avoid.
        # Instead, we just call update() to build the geometry.
        rndr.update(reset_camera=True)
        
        # 3. Export the PyVista plotter scene to an HTML file
        html_file = "pynite_render.html"
        rndr.plotter.export_html(html_file)
        
        # 4. Read the HTML file and display it in Streamlit
        with open(html_file, 'r') as f:
            html_data = f.read()
            
        components.html(html_data, height=800, width=1000)



if __name__ == "__main__":
    main()