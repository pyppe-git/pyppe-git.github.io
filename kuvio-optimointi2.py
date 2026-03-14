import geopandas as gpd
import numpy as np
from scipy.spatial.distance import cdist
import pulp
import matplotlib.pyplot as plt
# -----------------------------
# READ SHAPEFILE
# -----------------------------

# Fixed start point
start_point = np.array([638563.65, 6953924.40])


gdf = gpd.read_file("E:/maastokartta/kuviotest.shp")

# Keep required columns
gdf = gdf[["fid", "VOL", "DEVELOPMEN", "geometry"]]

# Convert polygons to centroids
gdf["geometry"] = gdf.geometry.centroid

# Drop invalid / zero prize rows if needed
gdf = gdf[gdf["VOL"] > 0].reset_index(drop=True)
# Original polygon centroids
centroids = np.array([(p.x, p.y) for p in gdf.geometry])

# Combine start point as node 0
coords = np.vstack([start_point, centroids])

# Prize: start point has 0 prize
prize = np.hstack([0, gdf["VOL"].to_numpy()])

# Class: start point as -1
classes_raw = np.hstack([-1, gdf["DEVELOPMEN"].to_numpy()])

# Encode classes (ignore start)
unique_classes, classes = np.unique(classes_raw[1:], return_inverse=True)
num_classes = len(unique_classes)

N = len(coords)
start = 0  # starting fid index

dist = cdist(coords, coords)

model = pulp.LpProblem("Shortest_Route_With_Coverage", pulp.LpMinimize)

# Visit node i
x = pulp.LpVariable.dicts("visit", range(N), 0, 1, pulp.LpBinary)

# Travel edge i -> j
y = pulp.LpVariable.dicts(
    "edge",
    ((i, j) for i in range(N) for j in range(N) if i != j),
    0, 1, pulp.LpBinary
)

# MTZ variables
u = pulp.LpVariable.dicts("u", range(N), 0, N - 1)

# -----------------------------
# OBJECTIVE: minimize distance
# -----------------------------
model += pulp.lpSum(dist[i][j] * y[(i, j)] for i, j in y)

# -----------------------------
# CONSTRAINTS
# -----------------------------

# Start node always visited
model += x[start] == 1

# Flow conservation (closed tour)
for i in range(N):
    model += pulp.lpSum(y[(i, j)] for j in range(N) if i != j) == x[i]
    model += pulp.lpSum(y[(j, i)] for j in range(N) if i != j) == x[i]

# Prize constraint (≥ 50%)
total_prize = prize.sum()
model += pulp.lpSum(prize[i] * x[i] for i in range(N)) >= 0.5 * total_prize

for c in range(num_classes):
    # +1 because coords[0] is start point
    model += pulp.lpSum(x[i+1] for i in range(N-1) if classes[i] == c) >= 1

# Subtour elimination (MTZ)
for i in range(N):
    for j in range(N):
        if i != j and i != start and j != start:
            model += u[i] - u[j] + (N - 1) * y[(i, j)] <= N - 2

solver = pulp.PULP_CBC_CMD(msg=True)
model.solve(solver)

visited = [i for i in range(N) if x[i].value() == 1]
edges = [(i, j) for (i, j) in y if y[(i, j)].value() == 1]

print("Visited fid values:")
print(gdf.loc[visited, "fid"].to_list())

print("Collected prize:", prize[visited].sum())
print("Visited classes:", set(classes_raw[visited]))

# Keep original polygons
gdf_polygons = gpd.read_file("E:/maastokartta/kuviotest.shp")

# Optional: filter only necessary columns if you like
gdf_polygons = gdf_polygons[["fid", "VOL", "DEVELOPMEN", "geometry"]]

# Plot all polygons
fig, ax = plt.subplots(figsize=(10, 10))

gdf_polygons.plot(ax=ax, facecolor="lightgray", edgecolor="black", alpha=0.6, label="All polygons")

# Plot centroids of visited polygons
visited_centroids = coords[visited]  # coords from optimization centroids
ax.scatter(visited_centroids[:, 0], visited_centroids[:, 1],
           color="red", s=80, label="Visited centroids")

# Start/end point
ax.scatter(coords[start, 0], coords[start, 1],
           color="blue", s=150, marker="*", label="Start/End")

# Draw route between centroids
for i, j in edges:
    x_line = [coords[i, 0], coords[j, 0]]
    y_line = [coords[i, 1], coords[j, 1]]
    ax.plot(x_line, y_line, color="black", linewidth=1.2, alpha=0.8)

# Labels (optional)
for i, row in gdf_polygons.iterrows():
    centroid = row.geometry.centroid
    ax.text(centroid.x + 0.5, centroid.y + 0.5, str(row["fid"]), fontsize=8)

ax.set_title("Polygons + Visited Centroids + Optimized Route")
ax.set_aspect("equal")
ax.legend()
plt.show()