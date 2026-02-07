import cadquery as cq

height = 10
l, w, t = 20 , 20 , 2
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
    #(0, 0)            # 9. Close the loop back to Start
]
part = cq.Workplane("front").polyline(bottom_points).close().extrude(height)

# --- DEBUGGING START ---
print("--- GEOMETRY DIAGNOSTIC ---")
print(f"1. Is Valid?      {part.val().isValid()}")
print(f"2. Shape Type:    {part.val().ShapeType()}") # Should be 'Solid'
print(f"3. Solid Count:   {part.solids().size()}")   # Should be 1
print(f"4. Volume:        {part.val().Volume()}")    # Should be > 0
print("---------------------------")
# --- DEBUGGING END ---