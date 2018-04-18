import json
import sys
import os
import math

size = 800

precedence = {
    "Circle": 0,
    "Polygon": 1,
    "Angle": 2,
    "Line": 3,
    "Point": 4
}

def to_hex(color):
    red = int(color[0]*255)
    green = int(color[1]*255)
    blue = int(color[2]*255)
    return '#{r:02x}{g:02x}{b:02x}'.format(r=red,g=green,b=blue)


def coordinate(val):
    """Converts [-1,1] to a real coordinate"""
    return int(size/2*val) + size/2

def lerp(x1, y1, x2, y2, t):
    return x1 + t*(x2-x1), y1+t*(y2-y1)

def dist(x1, y1, x2, y2):
    xs = (x1-x2)*(x1-x2)
    ys = (y1-y2)*(y1-y2)
    return math.sqrt(xs+ys)

def circumcircle(geometry, g):
    p1 = geometry[g['data']['p1']]['data']
    p2 = geometry[g['data']['p2']]['data']
    p3 = geometry[g['data']['p3']]['data']
    m1 = (p1['y']-p2['y'])/(p1['x']-p2['x'])
    m2 = (p3['y']-p2['y'])/(p3['x']-p2['x'])
    m1 = m1 if m1 != 0.0 else 10000000000000
    m2 = m2 if m2 != 0.0 else 10000000000000
    
    ma = -1.0*(1.0/m1)
    mb = -1.0*(1.0/m2)

    xa = 0.5*(p1['x']+p2['x'])
    ya = 0.5*(p1['y']+p2['y'])
    xb = 0.5*(p2['x']+p3['x'])
    yb = 0.5*(p2['y']+p3['y'])

    x = ((ma*xa)-(mb*xb)+yb-ya)/(ma-mb)
    y = (mb*(x-xb))+yb
    center = dict(data=dict(x=x, y=y))

    radius = dist(x, y, p1['x'], p1['y'])

    return center, radius

def point(g):
    point = '<circle cx="{0}" cy="{1}" r="{2}" fill="{3}"/>'
    x = coordinate(g['data']['x'])
    y = coordinate(g['data']['y'])
    color = to_hex(g['color'])
    text = '<text x="{0}" y="{1}" font-family="Verdana" font-size="20">{2}</text>'
    return point.format(x, y, size/100, color) + text.format(x+10, y-10, g['id'])

def circle(geometry, g):
    text = '<circle cx="{0}" cy="{1}" r="{2}" stroke="{3}" fill="{3}" fill-opacity="0" stroke-width="5"/>'
    radius = g['data']['radius']
    c = None
    if radius is None:
        c, radius = circumcircle(geometry, g)
    else:
        c = geometry[g['data']['center']]
    r = int(size/2 * radius)
    color = to_hex(g['color'])
    x = coordinate(c['data']['x'])
    y = coordinate(c['data']['y'])
    return text.format(x, y, r, color)


def line(geometry, g):
    text = '<line x1="{0}" y1="{1}" x2="{2}" y2="{3}" stroke="{4}" stroke-width="5"/>'
    color = to_hex(g['color'])
    c = geometry[g['data']['p1']]
    x1 = coordinate(c['data']['x'])
    y1 = coordinate(c['data']['y'])
    c = geometry[g['data']['p2']]
    x2 = coordinate(c['data']['x'])
    y2 = coordinate(c['data']['y'])
    return text.format(x1, y1, x2, y2, color)

def polygon(geometry, g):
    polygon = '<polygon points="{0}" stroke="{1}" stroke-width="5" fill="{1}" fill-opacity="0.2"/>'
    color = to_hex(g['color'])
    points = g['data']['points']
    text = ""
    for i in range(len(points)):
        p = geometry[points[i]]
        x = coordinate(p['data']['x'])
        y = coordinate(p['data']['y'])
        text += "{0},{1} ".format(x,y)
    return polygon.format(text, color)

def angle(geometry, g):
    path = '<path d="{0}" stroke="{1}" stroke-width="5" fill="none"/>'
    inner = 'M {sx} {sy} A {r} {r} 0 {large} {sweep} {ex} {ey}'

    color = to_hex(g['color'])
    p1, p2, p3 = [geometry[x]['data'] for x in g['data']['points']]
    cx = coordinate(p2['x'])
    cy = coordinate(p2['y'])
    x1 = coordinate(p3['x'])
    y1 = coordinate(p3['y'])
    x2 = coordinate(p1['x'])
    y2 = coordinate(p1['y'])
    
    d1 = dist(cx, cy, x1, y1)
    d2 = dist(cx, cy, x2, y2)
    radius = min(d1/3, d2/3)
    sweep = 1
    if d1 > d2:
        x1, x2, y1, y2 = x2, x1, y2, y1
        sweep = 0
        d1, d2 = d2, d1
    sx, sy = lerp(x1, y1, cx, cy, 0.7)
    ds = dist(cx, cy, sx, sy)
    ex = cx + (ds/d2)*(x2-cx)
    ey = cy + (ds/d2)*(y2-cy)

    d = dict(sx=sx, sy=sy, r=radius, large=0, sweep=sweep, ex=ex, ey=ey)

    return path.format(inner.format(**d), color)

    

def get_svg(geometry, to_draw):
    svg = '<svg width="{0}" height="{1}" xmlns="http://www.w3.org/2000/svg">'.format(size, size) + '{0}</svg>'
    shapes = ""
    to_draw.sort(key=lambda g: precedence[geometry[g]['type']])
    for name in to_draw:
        g = geometry[name]
        if g["type"] == "Point":
            shapes += point(g)
        elif g["type"] == "Circle":
            shapes += circle(geometry, g)
        elif g["type"] == "Line":
            shapes += line(geometry, g)
        elif g["type"] == "Polygon":
            shapes += polygon(geometry, g)
        elif g["type"] == "Angle":
            shapes += angle(geometry, g)
    return svg.format(shapes)

def write(name, svg):
    with open(name, "w") as f:
        f.write(svg)


def main(fname):
    f = open(fname, "r")
    text = f.read()
    f.close
    name = fname.split(".")[0]
    os.makedirs(name, exist_ok=True)
    geo = json.loads(text)
    svg = ""
    for i, step in enumerate(geo["animations"]):
        svg = get_svg(geo["geometry"], step)

        write("{0}/{0}_{1}.svg".format(name, i), svg)
        



if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Please give json files as args")
        exit()
    for i in range(1, len(sys.argv)):
        main(sys.argv[i])
