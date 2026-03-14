import numpy as np
import pulp
from scipy.spatial.distance import cdist

# -----------------------------
# DATA
# -----------------------------

np.random.seed(1)

N = 20
coords = np.random.rand(N, 2) * 100

prize = np.random.randint(1, 20, size=N)
classes = np.random.randint(0, 6, size=N)

start = 0

dist = cdist(coords, coords)

# -----------------------------
# MODEL
# -----------------------------

model = pulp.LpProblem("Prize_Collecting_TSP", pulp.LpMaximize)

# Visit node i
x = pulp.LpVariable.dicts("visit", range(N), 0, 1, pulp.LpBinary)

# Travel edge i -> j
y = pulp.LpVariable.dicts(
    "edge",
    ((i, j) for i in range(N) for j in range(N) if i != j),
    0, 1, pulp.LpBinary
)

# MTZ variables (subtour elimination)
u = pulp.LpVariable.dicts("u", range(N), 0, N - 1, cat="Continuous")

# -----------------------------
# OBJECTIVE
# -----------------------------
total_prize = sum(prize)
model += pulp.lpSum(prize[i] * x[i] for i in range(N)) >= 0.5 * total_prize

model += pulp.lpSum(dist[i][j] * y[(i, j)] for i, j in y)
model.sense = pulp.LpMinimize

# -----------------------------
# CONSTRAINTS
# -----------------------------

# Start node always visited
model += x[start] == 1

# Flow constraints
for i in range(N):
    model += pulp.lpSum(y[(i, j)] for j in range(N) if i != j) == x[i]
    model += pulp.lpSum(y[(j, i)] for j in range(N) if i != j) == x[i]

# Class coverage
for c in range(6):
    model += pulp.lpSum(x[i] for i in range(N) if classes[i] == c) >= 1

# Subtour elimination (MTZ)
for i in range(N):
    for j in range(N):
        if i != j and i != start and j != start:
            model += u[i] - u[j] + (N - 1) * y[(i, j)] <= N - 2

# -----------------------------
# SOLVE
# -----------------------------

solver = pulp.PULP_CBC_CMD(
    msg=True,          # turn on logging
    timeLimit=60,      # optional
    gapRel=0.0         # optional: require optimal
)

model.solve(solver)


# -----------------------------
# RESULTS
# -----------------------------

visited = [i for i in range(N) if x[i].value() == 1]

edges = [(i, j) for (i, j) in y if y[(i, j)].value() == 1]

print("Visited nodes:", visited)
print("Total prize:", sum(prize[i] for i in visited))
print("Visited classes:", set(classes[i] for i in visited))
print("Edges:", edges)


import matplotlib.pyplot as plt

# -----------------------------
# EXTRACT SOLUTION
# -----------------------------

visited = [i for i in range(N) if x[i].value() == 1]

edges = [(i, j) for (i, j) in y if y[(i, j)].value() == 1]

# -----------------------------
# PLOT
# -----------------------------

plt.figure(figsize=(8, 8))

# All points (background)
plt.scatter(coords[:, 0], coords[:, 1],
            s=40, alpha=0.4, label="All points")

# Visited points
visited_coords = coords[visited]
plt.scatter(visited_coords[:, 0], visited_coords[:, 1],
            s=120, marker="o", label="Visited points")

# Start/end point
plt.scatter(coords[start, 0], coords[start, 1],
            s=200, marker="*", label="Start / End")

# Draw route edges
for i, j in edges:
    x_line = [coords[i, 0], coords[j, 0]]
    y_line = [coords[i, 1], coords[j, 1]]
    plt.plot(x_line, y_line)

# Annotate node indices (optional but useful)
for i in range(N):
    plt.text(coords[i, 0] + 0.5, coords[i, 1] + 0.5, str(i), fontsize=9)

plt.title("Prize-Collecting Closed Route")
plt.xlabel("X")
plt.ylabel("Y")
plt.legend()
plt.grid(True)
plt.axis("equal")
plt.show()
