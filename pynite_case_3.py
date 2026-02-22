import sectionproperties.pre.library.steel_sections as steel_geom
from sectionproperties.analysis.section import Section

d = 30      # depth, inches
b = 4       # flange width, inches
t_f = 1.75  # flange thickness, inches
t_w = 1.5   # web thickness, inches

channel = steel_geom.channel_section(
    d=d,
    b=b,
    t_f=t_f,
    t_w=t_w,
    r=0,
    n_r=0
)

# View the section
channel

assembly_width = 12
double_channel = (
    channel.mirror_section(axis='y', mirror_point=(0,0)) +
    channel.shift_section(x_offset=assembly_width)
)

double_channel = double_channel.shift_section(x_offset=-assembly_width/2, y_offset=-d/2)

# View the section
double_channel.plot_geometry