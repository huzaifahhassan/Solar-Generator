from Pynite import FEModel3D
from Pynite.Rendering import Renderer


material = "Concrete"
E = 3600  # ksi
nu = 0.2
G = E / (2 * (1 + nu))  # ksi
rho = 3000

consider_axial_deformation = False
if consider_axial_deformation:
    axial_stiffness_factor = 1
else:
    axial_stiffness_factor = 1000


# Initialise model
frame_model = FEModel3D()

# Add nodes
frame_model.add_node("N1", X=0, Y=0, Z=0)
frame_model.add_node("N2", X=0, Y=0, Z=10*12)
frame_model.add_node("N3", X=8*12, Y=0, Z=16*12)
frame_model.add_node("N4", X=-4*12, Y=0, Z=10*12)

# Add material and section properties
frame_model.add_material(name=material, E=E, G=G, nu=nu, rho=rho)

frame_model.add_section(
    name="12x12",
    A=axial_stiffness_factor*12*12,
    Iy=12**3,
    Iz=12**3,
    J=2.25*(6**4)
)

# Add members
frame_model.add_member(
    name="M1",
    i_node="N1",
    j_node="N2",
    material_name="Concrete",
    section_name="12x12"
)
frame_model.add_member(
    "M2",
    i_node="N2",
    j_node="N3",
    material_name="Concrete",
    section_name="12x12"
)
frame_model.add_member(
    "M3",
    i_node="N4",
    j_node="N2",
    material_name="Concrete",
    section_name="12x12"
)

# Pin support
frame_model.def_support(
    "N1",
    support_DX=True,
    support_DY=True,
    support_DZ=True,
    support_RX=True,  # for stability
    support_RY=False,
    support_RZ=False,
)

# Roller support (free in z-direction)
frame_model.def_support(
    "N3",
    support_DX=True,
    support_DY=True,
    support_DZ=False,
    support_RX=False,
    support_RY=False,
    support_RZ=False,
)

# Add loads
frame_model.add_member_dist_load(
    "M3",
    direction="FZ",
    w1=-1.8 / 12,  # 1.8 klf to k/in
    w2=-1.8 / 12
)
frame_model.add_node_load(
    "N4",
    direction="FZ",
    P=-10,
)

# Run the model!
frame_model.analyze_linear(log=True, check_statics=True)


rndr = Renderer(frame_model)
rndr.annotation_size = 5
rndr.deformed_shape = True
rndr.deformed_scale = 100
rndr.render_nodes = True
rndr.render_loads = True
rndr.combo_name = 'Combo 1'
rndr.labels = True
rndr.render_model()