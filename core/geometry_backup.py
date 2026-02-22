import cadquery as cq
import plotly.graph_objects as go
import math
import streamlit as st


class GeometryEngine:
    """
    Handles the generation of 3D Structural components using CadQuery.
    Replaces: Manual Matrix Math with CAD Parametric Logic.
    """

    @staticmethod
    def _cq_to_plotly(cq_object, color, name):
        """
        Helper: Converts a CadQuery object into a Plotly Mesh3d.
        CadQuery objects are mathematical solids; Plotly needs triangles.
        """
        # 1. Tessellate: Convert the mathematical shape to vertices and triangles
        # tolerance: Determines how smooth curves are (0.1 is standard for viz)
        shape = cq_object.val()
        verts, triangles = shape.tessellate(tolerance=0.1)

        # 2. Extract X, Y, Z lists from the tessellation objects
        # verts is a list of cq.Vector objects
        x_vals = [v.x for v in verts]
        y_vals = [v.y for v in verts]
        z_vals = [v.z for v in verts]

        # 3. Extract Indices
        # triangles is a list of (i, j, k) tuples, we unzip them into lists
        i_vals = [t[0] for t in triangles]
        j_vals = [t[1] for t in triangles]
        k_vals = [t[2] for t in triangles]

        return go.Mesh3d(
            x=x_vals, y=y_vals, z=z_vals,
            i=i_vals, j=j_vals, k=k_vals,
            color=color,
            name=name,
            opacity=1.0,
            flatshading=True,
            lighting=dict(ambient=0.5, diffuse=1.0, specular=0.2)
        )

    @staticmethod
    def create_component_cq(center, length, width, height, color, tilt_angle= [], rot_tup = [], name="Component"):
        """
        Creates a solid Box using CadQuery, rotates it, and positions it.
        """
        # 1. Create a Box centered at (0,0,0)
        # CadQuery's .box() method creates a solid centered at the origin by default.
        # Dimensions: Y=length, X=width, Z=height
        part = cq.Workplane("XY").box(width, length, height)

        # 2. Apply Rotation (Tilt)
        # We rotate around the X-axis (1,0,0) at the origin (0,0,0)
        if len(tilt_angle) >= 0:
            for i in range(len(tilt_angle)):
                part = part.rotate((0, 0, 0), rot_tup[i], tilt_angle[i])

        # 3. Apply Translation (Move to final position)
        # Note: 'center' is the target coordinate (x, y, z)
        part = part.translate(center)

        # 4. Convert to Plotly for rendering
        return GeometryEngine._cq_to_plotly(part, color, name)
    
    @staticmethod
    def create_c_section_cq(center, length, width, height, thickness, color, rot_tup = [] , tilt_angle = [], name="C-Section"):
        """
        Creates a C-Channel by sketching exact coordinates on the XZ plane and extruding along Y.
        """
        # 1. Define the 8 exact coordinates of the C-Profile (Counter-Clockwise)
        # We start drawing at (0,0) which corresponds to the Bottom-Left corner
        l, w, t = length, width, thickness
        
        # 
        bottom_points = [
            (0, 0),           # 1. Bottom-Left (Start)
            (w, 0),           # 2. Bottom-Right Tip
            (w, t),           # 3. Bottom-Right Inner
            (t, t),           # 4. Inner Corner Bottom
            (t, l - t),       # 5. Inner Corner Top
            (w, l - t),       # 6. Top-Right Inner
            (w, l),           # 7. Top-Right Tip
            (0, l),           # 8. Top-Left
        ]

        top_points = [
            (0, 0),           # 1. Bottom-Left (Start)
            (w, 0),           # 2. Bottom-Right Tip
            (w, t),           # 3. Bottom-Right Inner
            (t, t),           # 4. Inner Corner Bottom
            (t, l - t),       # 5. Inner Corner Top
            (w, l - t),       # 6. Top-Right Inner
            (w, l),           # 7. Top-Right Tip
            (0, l),           # 8. Top-Left
        ]

        # 2. Create the Solid (LOFT)
        base_plane = cq.Workplane("XY").polyline(bottom_points).close()
        part = (
            base_plane                  # Connects the last point to the first
            .workplane(offset=height)  # Move the plane 'up' (along Y axis in this orientation)
            .polyline(top_points)
            .close()
            .loft(combine=True)        
        )

        # 2. Create the Solid (EXTRUDE)
        #part = cq.Workplane("front").polyline(bottom_points).close().extrude(height)

        # 3. Center the object locally
        # By default, the object is created starting at (0,0,0) extending to (+w, +length, +h).
        # We shift it backwards so its mathematical center is at (0,0,0). 
        # This makes rotation work as expected (rotating around its own center).
        part = part.translate((-width/2, -length/2, -height/2)) # This shows how much to translate in each axis

        # 4. Apply Rotation (Tilt)
        # Now that it is centered at (0,0,0), we can rotate around the Any-axis
        if len(tilt_angle) >= 0:
            for i in range(len(tilt_angle)):
                part = part.rotate((0, 0, 0), rot_tup[i], tilt_angle[i])

        # 5. Apply Final Translation (Move to global position)
        part = part.translate((center))

        # 6. Convert to Plotly
        return GeometryEngine._cq_to_plotly(part, color, name)

    @staticmethod
    def generate_structure(params):
        """
        Main logic function using CadQuery.
        """
        meshes = []
        
        # --- 1. Unpack Parameters ---
        # Panel
        p_len = params['panel_length']
        p_wid = params['panel_width']
        p_thk = params['panel_thickness']
        
        # Configuration
        angle = params['angle']
        angle_rad = math.radians(angle)
        rows = int(params['rows'])
        cols = int(params['cols'])
        
        # Offsets
        front_off = params['front_offset']
        rear_off = params['rear_offset']
        purlin_off = params['purlin_offset']
        rafter_purlin_off = params['rafter_purlin_offset']
        hor_panel_overhang = params['hor_panel_overhang']
        hor_purlin_overhang = params['hor_purlin_overhang']
        
        # Spacing
        h_gap = params['h_gap']
        v_gap = params['v_gap']
        
        # Structure Sizes
        col_h_min = params['col_min_height']

        col_len = params['col_len']
        col_wid = params['col_wid']
        col_thk = params['col_thk']

        raf_len = params['raf_len']
        raf_wid = params['raf_wid']
        raf_thk = params['raf_thk']

        pur_len = params['pur_len']
        pur_wid = params['pur_wid']
        pur_thk = params['pur_thk']

        # Block Dimensions
        blk_len = params['blk_len']
        blk_wid = params['blk_wid']
        blk_height = params['blk_heigth']
        
        # Layout
        y_cols_count = int(params['y_cols'])
        x_cols_count = int(params['x_cols'])

        # Solar Farm Layout
        copies_in_x = int(params['copies_in_x'])
        x_gap = params['x_gap']
        copies_in_y = int(params['copies_in_y'])
        y_gap = params['y_gap']

        # --- 2. Calculate Derived Dimensions ---
        horiz_spacing = p_wid + h_gap
        vert_spacing = p_len + v_gap
        total_width = cols * horiz_spacing - h_gap - 2*hor_panel_overhang
        total_slope_length = rows * vert_spacing - v_gap

        total_ground_length = total_slope_length * math.cos(angle_rad)

        # Colors
        C_PANEL = "#e0b14b" 
        C_COLUMN = "#C44646"
        C_PURLIN = "#379c09" 
        C_RAFTER = "#2292DD"
        C_BLOCK =  "#00AB8F"

        # --- 3. -------------------------GENERATE COLUMNS & BLOCKS (Using CadQuery) --------------------------------
        div_y = max(1, y_cols_count - 1)
        div_x = max(1, x_cols_count - 1)
        
        y_spacing_ground = (total_ground_length - (front_off + rear_off) * math.cos(angle_rad)) / div_y  # If this is center to center spacing then it is fine
        x_spacing = (total_width) / div_x if div_x > 0 else 0  # This is not center to center spacing

        # OUTER LOOPS TO CREATE A SOLAR FARM
        for i in range(copies_in_x):
            for j in range(copies_in_y):

                for y_i in range(y_cols_count):
                    for x_i in range(x_cols_count):

                        cx = hor_panel_overhang + x_i * x_spacing - raf_wid if x_cols_count > 1 else total_width / 2  
                        cy = (front_off * math.cos(angle_rad)) + (y_i * y_spacing_ground)
                        calculated_height = col_h_min + (cy * math.tan(angle_rad))
                        

                        # CREATING COLUMN
                        # Use CadQuery builder (C-SECTION) 
                        meshes.append(GeometryEngine.create_c_section_cq(
                            center=(cx + x_gap*(i), cy + y_gap*(j), calculated_height / 2),
                            length=col_len, # Y dimension
                            width=col_wid,  # X dimension
                            thickness=col_thk,
                            rot_tup= [(0,0,1)],
                            tilt_angle= [180],
                            height=calculated_height, # Z dimension
                            color=C_COLUMN,
                            name="Column"
                        ))

                        # CREATING BLOCKS

                        block_z_center = -(blk_height / 2)
                        
                        # # Use CadQuery builder (BOX)
                        meshes.append(GeometryEngine.create_component_cq(
                            center=(cx + x_gap*(i), cy + y_gap*(j), block_z_center),
                            length=blk_len, # Y dimension
                            width=blk_wid,  # X dimension
                            height=blk_height, # Z dimension
                            color=C_BLOCK,
                            name="Block"
                        ))


        # --- 4. -------------------------GENERATE RAFTERS (Using CadQuery) -------------------------------

        rafter_off = purlin_off - rafter_purlin_off

        print(rafter_off)

        for i in range(copies_in_x):
            for j in range(copies_in_y):


                rafter_mid_z = col_h_min + (total_ground_length * math.tan(angle_rad)) / 2 + raf_len / 2
                rafter_mid_y =  (rafter_off * math.cos(angle_rad) if rafter_off > 0 else 0) + (total_ground_length - 2*rafter_off*math.cos(angle_rad)) / 2
                rafter_height = total_slope_length - 2*rafter_off

                for x_i in range(x_cols_count):
                    rx = hor_panel_overhang + x_i * x_spacing if x_cols_count > 1 else total_width / 2

                    meshes.append(GeometryEngine.create_c_section_cq(
                        center=(rx+x_gap*(i), rafter_mid_y + y_gap*(j), rafter_mid_z),
                        length=raf_len, # Rafters are long along Y (before tilt)
                        width=raf_wid,
                        height=rafter_height,
                        thickness=raf_thk,
                        rot_tup= [(1,0,0)],
                        color=C_RAFTER,
                        tilt_angle= [90 + angle],
                        name="Rafter"
                    ))

        # --- 5. -------------------------- GENERATE PURLINS (Using CadQuery) ---------------------------------
        purlin_spacing = (p_len - purlin_off*2)*math.cos(angle_rad)

        for i in range(copies_in_x):
            for j in range(copies_in_y):

                for row in range(0, rows):

                    pur_y_pos_1 = (row)*(p_len+v_gap)*math.cos(angle_rad) + purlin_off*math.cos(angle_rad)
                    pur_y_pos_2 = pur_y_pos_1 + purlin_spacing
                    pur_z_pos_1 = col_h_min + pur_y_pos_1*math.tan(angle_rad) + raf_len*1.5
                    pur_z_pos_2 = col_h_min + pur_y_pos_2*math.tan(angle_rad) +  raf_len*1.5

                    meshes.append(GeometryEngine.create_c_section_cq(
                            center=(hor_panel_overhang + total_width / 2 + x_gap*(i), pur_y_pos_1 + y_gap*(j), pur_z_pos_1),
                            length=pur_len, # Purlin depth (cross section)
                            width=pur_wid, # Purlin spans the whole width
                            thickness=pur_thk,
                            height=total_width + 2*hor_purlin_overhang,
                            rot_tup = [(0,1,0), (1,0,0)], # Rotation about Y
                            color=C_PURLIN,
                            tilt_angle= [90, angle+90],
                            name="Purlin"
                        ))
                    
                    
                    meshes.append(GeometryEngine.create_c_section_cq(
                            center=(hor_panel_overhang + total_width / 2 + x_gap*(i), pur_y_pos_2 + y_gap*(j), pur_z_pos_2),
                            length=pur_len, 
                            width=pur_wid, 
                            thickness=pur_thk,
                            height=total_width + 2*hor_purlin_overhang,
                            rot_tup = [(0,1,0), (1,0,0)], # Rotation about Y
                            color=C_PURLIN,
                            tilt_angle= [90, angle+90],
                            name="Purlin"
                        ))


        # --- 6. ---------------------------- GENERATE PANELS (Using CadQuery) -----------------------------

        for i in range(copies_in_x):
            for j in range(copies_in_y):

                for r in range(rows):
                    for c in range(cols):
                        local_y = r * vert_spacing + p_len / 2
                        local_x = c * horiz_spacing + p_wid / 2
                        
                        pan_y = local_y * math.cos(angle_rad)
                        stack_height = raf_len + pur_len + (p_thk / 2) + 0.02
                        pan_z = col_h_min + (local_y * math.sin(angle_rad)) + stack_height
                        
                        meshes.append(GeometryEngine.create_component_cq(
                            center=(local_x + x_gap*(i), pan_y + y_gap*(j), pan_z),
                            length=p_len,
                            width=p_wid,
                            height=p_thk,
                            color=C_PANEL,
                            tilt_angle=[angle],
                            rot_tup= [(1,0,0)],
                            name=f"Panel R{r+1}C{c+1}"
                        ))
                
        return meshes