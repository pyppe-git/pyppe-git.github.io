import geopandas as gpd
from shapely.geometry import Point, Polygon
import numpy as np
from scipy.spatial import Voronoi


gdf = gpd.read_file("E:/maastokartta/input_polygon.shp")
polygon = gdf.geometry.iloc[0]

assert polygon.is_valid

def random_points_in_polygon(poly, n):
    minx, miny, maxx, maxy = poly.bounds
    pts = []
    while len(pts) < n:
        p = Point(
            np.random.uniform(minx, maxx),
            np.random.uniform(miny, maxy)
        )
        if poly.contains(p):
            pts.append(p)
    return pts

N = 10
points = random_points_in_polygon(polygon, N)

def create_dummy_points(polygon, margin_factor=3, points_per_side=10):
    minx, miny, maxx, maxy = polygon.bounds
    width = maxx - minx
    height = maxy - miny

    margin = max(width, height) * margin_factor

    xs = np.linspace(minx - margin, maxx + margin, points_per_side)
    ys = np.linspace(miny - margin, maxy + margin, points_per_side)

    dummy_points = []

    # ylä ja ala
    for x in xs:
        dummy_points.append(Point(x, miny - margin))
        dummy_points.append(Point(x, maxy + margin))

    # vasen ja oikea
    for y in ys:
        dummy_points.append(Point(minx - margin, y))
        dummy_points.append(Point(maxx + margin, y))

    return dummy_points

def clipped_voronoi_with_dummy(points, polygon):
    dummy_points = create_dummy_points(polygon)

    all_points = points + dummy_points
    coords = np.array([[p.x, p.y] for p in all_points])

    vor = Voronoi(coords)

    cells = []

    for i in range(len(points)):  # VAIN oikeat pisteet
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]

        if len(region) == 0 or -1 in region:
            cells.append(None)
            continue

        poly = Polygon([vor.vertices[v] for v in region])
        cells.append(poly.intersection(polygon))

    return cells


def lloyd_iteration(points, polygon, iterations=30, alpha=0.3):
    for _ in range(iterations):
        cells = clipped_voronoi_with_dummy(points, polygon)

        new_points = []
        for p, cell in zip(points, cells):
            if cell is None or cell.area == 0:
                new_points.append(p)
                continue

            c = cell.centroid
            new_points.append(
                Point(
                    p.x + alpha * (c.x - p.x),
                    p.y + alpha * (c.y - p.y)
                )
            )

        points = new_points

    return points, clipped_voronoi_with_dummy(points, polygon)


TARGET_AREA = polygon.area / N

def area_relax(points, poly, steps=10):
    for _ in range(steps):
        cells = clipped_voronoi_with_dummy(points, poly)
        for i, cell in enumerate(cells):
            if cell is None:
                continue
            diff = cell.area - TARGET_AREA
            dx = (points[i].x - poly.centroid.x)
            dy = (points[i].y - poly.centroid.y)
            points[i] = Point(
                points[i].x - 0.001 * diff * dx,
                points[i].y - 0.001 * diff * dy
            )
    return points

points, cells = lloyd_iteration(points, polygon)

out = gpd.GeoDataFrame(
    geometry=cells,
    crs=gdf.crs
)
out.to_file("E:/maastokartta/equal_area_cells4.shp")
