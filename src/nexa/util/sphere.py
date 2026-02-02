import math

def distribute_points_on_sphere(n):
    if n <= 0:
        return []
    
    phi = (1 + math.sqrt(5)) / 2  # Golden ratio
    points = []
    
    for i in range(n):
        z = 1 - (2 * i + 1) / n  # Linear spacing in z for equal area projection
        theta = 2 * math.pi * i / phi  # Golden angle increment
        r = math.sqrt(1 - z**2)  # Radius at this latitude
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        points.append((x, y, z))
    
    return points

# Example usage:
# points = distribute_points_on_sphere(100)
# print(points)