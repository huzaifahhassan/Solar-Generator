import cadquery as cq
import plotly.graph_objects as go
import math
import streamlit as st
import numpy as np
from Pynite import FEModel3D


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
    def create_nodes_plotly(nodes_list, color="red", size=6, name="FEA Nodes"):
        """
        Helper: Converts a list of [x, y, z] coordinates into a Plotly Scatter3d object.
        Used for validating structural nodes.
        """
        if not nodes_list:
            return None

        # Unpack the list of lists/tuples into separate X, Y, Z lists
        x_vals = [p[0] for p in nodes_list]
        y_vals = [p[1] for p in nodes_list]
        z_vals = [p[2] for p in nodes_list]

        return go.Scatter3d(
            x=x_vals, y=y_vals, z=z_vals,
            mode='markers',
            marker=dict(
                size=size,
                color=color,
                symbol='circle',
                line=dict(width=1, color='DarkSlateGrey') # Adds a nice border to the nodes
            ),
            name=name
        )

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

                column_heights = []
                column_y_pos = []

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

                    column_heights.append(calculated_height) # From Shortest to Tallest in the Y-Axis
                    column_y_pos.append(cy) # From Shortest to Tallest in the Y-Axis


        # --- 4. -------------------------GENERATE RAFTERS (Using CadQuery) -------------------------------

        rafter_off = purlin_off - rafter_purlin_off

        print(rafter_off)

        rafter_x_nodes = []

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

                    rafter_x_nodes.append(rx)


    # --- 6. ---------------------------- GENERATE PANELS (Using CadQuery) -----------------------------
        x_coords = []

        for i in range(copies_in_x):
            for j in range(copies_in_y):

                for c in range(cols):
                    for r in range(rows):
                        local_y = r * vert_spacing + p_len / 2
                        local_x = c * horiz_spacing + p_wid / 2 # horiz_spacing = p_wid + h_gap

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

                    x_coord = local_x - p_wid/2 - h_gap/2 if c > 1 else local_x - p_wid/2
                    x_coords.append(x_coord)

                panel_x_coords = x_coords[:] # This is redundant right now will need to fix the looping



        # --- 5. -------------------------- GENERATE PURLINS (Using CadQuery) ---------------------------------
        purlin_spacing = (p_len - purlin_off*2)*math.cos(angle_rad)
        raf_pur_inter_points = []
        pur_points = []
        column_coords = []
        pur_pan_inter_points = []


        for i in range(copies_in_x):
            for j in range(copies_in_y):

                for row in range(0, rows):

                    up_per_points = []
                    low_per_points = []


                    pur_y_pos_1 = (row)*(p_len+v_gap)*math.cos(angle_rad) + purlin_off*math.cos(angle_rad)
                    pur_y_pos_2 = pur_y_pos_1 + purlin_spacing
                    pur_z_pos_1 = col_h_min + pur_y_pos_1*math.tan(angle_rad) + raf_len*1.5
                    pur_z_pos_2 = col_h_min + pur_y_pos_2*math.tan(angle_rad) +  raf_len*1.5


                    ### UPPER PERLIN
                    cx = hor_panel_overhang + total_width / 2
                    cy = pur_y_pos_1
                    cz = pur_z_pos_1
                    perlin_height = total_width + 2*hor_purlin_overhang

                    meshes.append(GeometryEngine.create_c_section_cq(
                            center=(cx, cy, cz),
                            length=pur_len, # Purlin depth (cross section)
                            width=pur_wid, # Purlin spans the whole width
                            thickness=pur_thk,
                            height= perlin_height,
                            rot_tup = [(0,1,0), (1,0,0)], # Rotation about Y
                            color=C_PURLIN,
                            tilt_angle= [90, angle+90],
                            name="Purlin"
                        ))
                    
                    p_upper_center = [cx,cy,cz]
                    p_upper_end_left = [cx - perlin_height/2, cy, cz]
                    p_upper_end_right = [cx + perlin_height/2, cy, cz]
                    up_per_points = [p_upper_end_left,p_upper_end_right]
                    up_per_raf_points = [[x, cy, cz] for x in rafter_x_nodes]
                    upper_per_pan_points = [[x, cy, cz] for x in panel_x_coords]



                    ### LOWER PERLIN
                    cy = pur_y_pos_2
                    cz = pur_z_pos_2

                    meshes.append(GeometryEngine.create_c_section_cq(
                            center=(cx, cy, cz),
                            length=pur_len, 
                            width=pur_wid, 
                            thickness=pur_thk,
                            height=total_width + 2*hor_purlin_overhang,
                            rot_tup = [(0,1,0), (1,0,0)], # Rotation about Y
                            color=C_PURLIN,
                            tilt_angle= [90, angle+90],
                            name="Purlin"
                        ))
                    
                    p_lower_center = [cx,cy,cz]
                    p_lower_end_left = [cx - perlin_height/2, cy, cz]
                    p_lower_end_right = [cx + perlin_height/2, cy, cz]
                    low_per_points = [p_lower_end_left,p_lower_end_right]
                    low_per_raf_points = [[x, cy, cz] for x in rafter_x_nodes]
                    lower_per_pan_points = [[x, cy, cz] for x in panel_x_coords]


                            
                    # RAFTER - PURLIN INTERSECTION POINTS
                    temp_list = [up_per_raf_points, low_per_raf_points]
                    raf_pur_inter_points.append(temp_list) # These are the points of intersection of rafter and purlin for all rafter and purlins
                    # PURLIN END POINTS
                    temp_list = [up_per_points, low_per_points]
                    pur_points.append(temp_list)
                    # PANEL - PURLIN INTERSECTION POINTS
                    temp_list = [upper_per_pan_points, lower_per_pan_points]
                    pur_pan_inter_points.append(temp_list)


                    

                # Equation = z = my + c
                m = (low_per_raf_points[0][2] - up_per_raf_points[0][2]) / (low_per_raf_points[0][1] - up_per_raf_points[0][1])
                c = low_per_raf_points[0][2] - m*low_per_raf_points[0][1]
                column_top_height = m*np.array(column_y_pos) + c

                print(f"Gradient: {m}, Intercept: {c}")
                print(f"Column Heights: {column_heights}")
                print(f"Column Y-Positions: {column_y_pos}")
                print(f"Upper Column Height: {column_top_height}")



                # Now we need to attch the bottom z to its corresponding x and y
                for x in rafter_x_nodes:
                    for i in range(len(column_y_pos)):
                        column_coords.append([[x,column_y_pos[i],0],[x,column_y_pos[i],column_top_height[i]]])
                

        

        # Putting all Nodes in one list
        all_fea_nodes = []
        for i in range(len(raf_pur_inter_points)):
            for j in range(len(raf_pur_inter_points[i])):
                for k in range(len(raf_pur_inter_points[i][j])):
                    all_fea_nodes.append(raf_pur_inter_points[i][j][k])

        for i in range(len(pur_points)):
            for j in range(len(pur_points[i])):
                for k in range(len(pur_points[i][j])):
                    all_fea_nodes.append(pur_points[i][j][k])

        for i in range(len(pur_pan_inter_points)):
            for j in range(len(pur_pan_inter_points[i])):
                for k in range(len(pur_pan_inter_points[i][j])):
                    all_fea_nodes.append(pur_pan_inter_points[i][j][k])
        
        for i in range(len(column_coords)):
            for j in range(len(column_coords[i])):
                all_fea_nodes.append(column_coords[i][j])

        # Node Categories
        # 1. Load Application Nodes ( pur_pan_inter_points )
        # 2. Boundary Condition Nodes ( column_coords )

        # Creating Nodes
        node_trace = GeometryEngine.create_nodes_plotly(all_fea_nodes)
        if node_trace:
            meshes.append(node_trace)

        # CREATING MEMBERS FROM NODES

        # Creating MEMBERS ALONG PURLINS
        # We will start with Upper Purlin. We will go left to right
        # We will get Purlin Endpoints at the far ends ( simple to add to it )
        # We will get Purlin Rafter Intersections 
        # We will get Purlin Panel Intersections (We need to save these intersections in a list so we exactly know which nodes to apply load on)

        # We first need to merge purlin endpoints , pur_raf_inter , pur_pan_inter in ascending order in X axis
        # After sorting we need to make members
        # We need to do this for each purlin

        ### PYNITE GENERAL PROPERTIES
        model = FEModel3D()

        ## NAMING SCHEME
        # Purlin Nodes : P_N_{x:.3f}_{y:.3f}_{z:.3f}
        # Rafter Nodes : R_N_{x:.3f}_{y:.3f}_{z:.3f}
        # Column Nodes : C_N_{x:.3f}_{y:.3f}_{z:.3f}
        # Block Nodes : B_N_{x:.3f}_{y:.3f}_{z:.3f}

        ############################################### BUILDING PURLINS #######################################

        # ADDING PURLIN MATERIAL
        material = "purlin_mat"
        E = 29_000  # ksi
        nu = 0.3
        G = E / (2 * (1 + nu)) # ksi
        rho = 0.49 / (12**3)   # kci

        model.add_material(name=material, E=E, G=G, nu=nu, rho=rho)

        # ADDING PURLIN SECTION
        model.add_section("purlin_sec", A=10.3, Iy=15.3, Iz=510, J=0.506)

        # DEFINING PURLIN ANGLE ABOUT ITS AXIS
        purlin_angle = angle + 90

        # PURLIN NODE PROCESS 
        for i in range(len(pur_points)):
            for j in range(len(pur_points[i])):
                one_purlin_nodes = []
                # Adding Left Purlin Endpoint
                one_purlin_nodes.append(pur_points[i][j][0])
                # Converting To Numpy and Sorting
                r_p_points = np.array(raf_pur_inter_points[i][j])
                print(f"RP POINTS: {r_p_points} ########")
                p_p_points = np.array(pur_pan_inter_points[i][j])
                print(f"PP POINTS: {p_p_points} ########")
                concat_points = np.concatenate((r_p_points, p_p_points), axis=0)
                # Sorting the points along x dimension
                sorted_indexes = concat_points[:,0].argsort()
                sorted_points = concat_points[sorted_indexes].tolist()
                # Adding points to one_purlin_nodes list
                for k in range(len(sorted_points)):
                    one_purlin_nodes.append(sorted_points[k])
                # Adding Right Purlin Endpoint
                one_purlin_nodes.append(pur_points[i][j][1])
                print(np.array(one_purlin_nodes))

                # ADDING PURLIN NODES
                node_names = []
                for p in range(len(one_purlin_nodes)):
                    x = one_purlin_nodes[p][0]
                    y = one_purlin_nodes[p][1]
                    z = one_purlin_nodes[p][2]
                    node = f"N_{x:.3f}_{y:.3f}_{z:.3f}" 
                    try: # This automatically filters duplicate nodes by name
                        model.add_node(node, x, y, z)
                        node_names.append(node)
                    except:
                        None

                # ADDING PURLIN MEMBERS
                for q in range(len(node_names)-1):
                    model.add_member(
                        f"M_{node_names[q]}_{node_names[q+1]}",
                        i_node=node_names[q],
                        j_node=node_names[q+1],
                        material_name="purlin_mat", 
                        section_name="purlin_sec", 
                        rotation= purlin_angle, 
                        tension_only=False,
                        comp_only=False
                    )

        ######################################### BUILDING RAFTERS ###############################################
                
        # ADDING RAFTER MATERIAL
        material = "rafter_mat"
        E = 29_000  # ksi
        nu = 0.3
        G = E / (2 * (1 + nu)) # ksi
        rho = 0.49 / (12**3)   # kci

        model.add_material(name=material, E=E, G=G, nu=nu, rho=rho)

        # ADDING RAFTER SECTION
        model.add_section("rafter_sec", A=10.3, Iy=15.3, Iz=510, J=0.506)

        # DEFINING RAFTER ANGLE ABOUT ITS AXIS
        rafter_angle = 0

        # RAFTER NODE PROCESS
        for i in range(x_cols_count): 

            one_rafter_nodes = []
            one_rafter_names = []
            for j in range(len(raf_pur_inter_points)):
                for k in range(2):
                    raf_point = raf_pur_inter_points[j][k][i]
                    x = raf_point[0]
                    y = raf_point[1]
                    z = raf_point[2]
                    node_name = f"N_{x:.3f}_{y:.3f}_{z:.3f}" 
                    one_rafter_names.append(node_name)
                    one_rafter_nodes.append(raf_point)

            for c in range(y_cols_count):
                column_node = column_coords[i][c]
                x = column_node[0]
                y = column_node[1]
                z = column_node[2]
                node_name = f"N_{x:.3f}_{y:.3f}_{z:.3f}"
                one_rafter_names.append(node_name) 
                model.add_node(node_name, x, y, z)
                one_rafter_nodes.append(column_node)

                # Now we have saved Column nodes and Rafter Nodes. We now have to Sort Node List and Node Names
                # Then make members using sorted Node Names
                # Where ever we have a column Node. We need to make the column member right there and then. 

            # ADDING RAFTER MEMBERS (TO BE MODIFIED FOR UPDATED LOGIC ABOVE)
            for q in range(len(node_names)-1):
                model.add_member(
                    f"M_{node_names[q]}_{node_names[q+1]}",
                    i_node=node_names[q],
                    j_node=node_names[q+1],
                    material_name="rafter_mat", 
                    section_name="rafter_sec", 
                    rotation= rafter_angle, 
                    tension_only=False,
                    comp_only=False
                )

                    
        return meshes, all_fea_nodes