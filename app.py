import streamlit as st
import plotly.graph_objects as go
from core.geometry import GeometryEngine
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
        with st.expander("Offsets & Spacing"):
            h_gap = st.number_input("Panel H-Gap", 0.0, 0.1, 0.02)
            v_gap = st.number_input("Panel V-Gap", 0.0, 0.1, 0.02)
            st.markdown("---")
            front_off = st.number_input("Front Column Offset", 0.0, 2.0, 0.3)
            rear_off = st.number_input("Rear Column Offset", 0.0, 2.0, 0.3)
            purlin_off = st.number_input("Purlin Offset", 0.0, 1.0, 0.3)
            rafter_purlin_off = st.number_input("Rafter-Purlin Offset", 0.0, 2.0, 0.2)
            hor_panel_off = st.number_input("Horizontal Panel Overhang", 0.0, 2.0, 0.2)
            hor_purlin_off = st.number_input("Horizontal Purlin Overhang", 0.0, 2.0, 0.2)

        # --- Section: Structure Details ---
        with st.expander("Solar Farm Details"):
            copies_in_x = st.number_input("Duplicates in X", 1, 10, 1)
            x_gap = st.number_input("Gap in X" , 0.0, 50.0, 20.0)
            copies_in_y = st.number_input("Duplicates in Y", 1, 10, 1)
            y_gap = st.number_input("Gap in Y", 0.0, 50.0, 20.0)

        with st.expander("RCC Block Details"):
            b_len, b_wid, b_high = st.columns(3)
            blk_len = b_len.number_input("Block Length", 0.5, 5.0, 1.0)
            blk_wid = b_wid.number_input("Block Width", 0.5, 5.0, 1.0)
            blk_heigth = b_high.number_input("Block Height", 0.5, 5.0, 1.0)

        with st.expander("Section Profiles"):
            
            st.subheader("Column Cross Section (m)")
            c_len, c_wid, c_thk = st.columns(3)
            col_len = c_len.number_input("Column Length", 0.05, 0.5, 0.15)
            col_wid = c_wid.number_input("Column Width", 0.05, 0.5, 0.15)
            col_thk = c_thk.number_input("Column Thickness", 0.01, 0.5, 0.01)

            st.subheader("Rafter Cross Section (m)")
            r_len, r_wid, r_thk = st.columns(3)
            raf_len = r_len.number_input("Rafter Length", 0.05, 0.5, 0.15)
            raf_wid = r_wid.number_input("Rafter Width", 0.05, 0.5, 0.15)
            raf_thk = r_thk.number_input("Rafter Thickness", 0.01, 0.5, 0.01)

            st.subheader("Purlin Cross Section (m)")
            pr_len, pr_wid, pr_thk = st.columns(3)
            pur_len = pr_len.number_input("Purlin Length", 0.05, 0.5, 0.15)
            pur_wid = pr_wid.number_input("Purlin Width", 0.05, 0.5, 0.15)
            pur_thk = pr_thk.number_input("Purlin Thickness", 0.01, 0.5, 0.01)

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
        'front_offset': front_off, 'rear_offset': rear_off, 'purlin_offset': purlin_off, 'rafter_purlin_offset': rafter_purlin_off, 'hor_panel_overhang': hor_panel_off, 'hor_purlin_overhang': hor_purlin_off,
        'col_len': col_len, 'col_wid': col_wid, 'col_thk': col_thk,
        'raf_len': raf_len, 'raf_wid': raf_wid, 'raf_thk': raf_thk,
        'pur_len': pur_len, 'pur_wid': pur_wid, 'pur_thk': pur_thk,
        'copies_in_x': copies_in_x, 'copies_in_y': copies_in_y, 'x_gap': x_gap, 'y_gap': y_gap,
        'blk_len': blk_len, 'blk_wid': blk_wid, 'blk_heigth': blk_heigth,
    }

    # Call the Engine
    try:
        geometry_meshes = GeometryEngine.generate_structure(params)
    except Exception as e:
        st.error(f"Error generating geometry: {e}")
        st.stop()

    # ==========================================
    # 3. VISUALIZATION - PLOTLY 3D
    # ==========================================
    
    # Create the figure
    fig = go.Figure(data=geometry_meshes)

    # Update Layout for Engineering View (Aspect Ratio is Key!)
    fig.update_layout(
        scene=dict(
            aspectmode='data', # Ensures 1 meter looks like 1 meter on all axes
            xaxis=dict(title="X (Width)", backgroundcolor="rgb(240, 240, 240)"),
            yaxis=dict(title="Y (Depth)", backgroundcolor="rgb(240, 240, 240)"),
            zaxis=dict(title="Z (Height)", backgroundcolor="rgb(230, 230, 250)"),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2) # Initial camera position
            )
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=700, # Height of the canvas in pixels
    )

    # Render
    st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # 4. SUMMARY METRICS
    # ==========================================
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Panels", rows * cols)
    c2.metric("System Area", f"{(rows * cols * p_len * p_wid):.2f} m²")
    # A placeholder for future steps
    c3.button("Calculate Wind Loads ➔", help="Feature coming in Step 3")

if __name__ == "__main__":
    main()