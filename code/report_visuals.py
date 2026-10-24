"""Exact report floorplan and illustrative legal routes, with fixed landmarks."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def graph_edges(graph):
    return {tuple(sorted((a, b))) for a, neighbors in graph.items() for b in neighbors}


def segments_intersect(a, b, c, d):
    def cross(p, q, r):
        return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    def on_segment(p, q, r):
        return min(p[0],q[0]) <= r[0] <= max(p[0],q[0]) and min(p[1],q[1]) <= r[1] <= max(p[1],q[1])
    values = [cross(a,b,c), cross(a,b,d), cross(c,d,a), cross(c,d,b)]
    if values[0]*values[1] < 0 and values[2]*values[3] < 0:
        return True
    return any(v == 0 and on_segment(p,q,r) for v,p,q,r in [
        (values[0],a,b,c),(values[1],a,b,d),(values[2],c,d,a),(values[3],c,d,b)])


def validate_scene(graph, scene):
    doors = {tuple(sorted(door["rooms"])): door["point"] for door in scene["doorways"]}
    if set(doors) != graph_edges(graph):
        raise ValueError("Illustrated doorways do not match the experiment graph")
    x0,y0,x1,y1 = scene["bounds"]
    for route in scene["routes"]:
        if route["points"][0] != scene["robot"] or route["points"][-1] != scene["destination"]:
            raise ValueError("Every illustrated route must join the fixed robot and destination")
        for a,b in zip(route["states"], route["states"][1:]):
            edge = tuple(sorted((a,b)))
            if edge not in doors or doors[edge] not in route["points"]:
                raise ValueError("Route omits a real doorway or contains an illegal move")
        for point in route["points"]:
            if not (x0 < point[0] < x1 and y0 < point[1] < y1):
                raise ValueError("Route leaves the floorplan")
        for a,b in zip(route["points"],route["points"][1:]):
            for xa,ya,xb,yb in scene["walls"]:
                if segments_intersect(a,b,[xa,ya],[xb,yb]):
                    raise ValueError(f"Route {route['id']} crosses a wall")
    return True


def route_scene(graph):
    scene = json.loads((ROOT / "configs/floorplan.json").read_text())
    validate_scene(graph, scene)
    svg = ['<svg id="route-scene" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 540" role="img" aria-labelledby="scene-title scene-description">',
           '<title id="scene-title">Three possible routes through the corrected room map</title>',
           '<desc id="scene-description">The robot stays in C and the dock stays in F. Doorways connect A-E, B-C, B-D, B-F, C-D, D-E, E-F. Teal follows C-B-F; orange follows C-D-B-F; blue follows C-D-E-F. Translucent moving echoes fade at the destination. The routes illustrate legal choices, not recorded runs.</desc>',
           '<defs><filter id="wall-shadow" x="-15%" y="-15%" width="140%" height="150%"><feDropShadow dx="0" dy="5" stdDeviation="3" flood-color="#59685e" flood-opacity=".17"/></filter>',
           '<radialGradient id="dock-light"><stop stop-color="#dbaa56" stop-opacity=".27"/><stop offset="1" stop-color="#dbaa56" stop-opacity="0"/></radialGradient>',
           '<linearGradient id="floor-fill" x2="0" y2="1"><stop stop-color="#f2f0e7"/><stop offset="1" stop-color="#e9e9de"/></linearGradient>']
    for route in scene["routes"]:
        color = route["color"]
        svg.append(f'<linearGradient id="fade-{route["id"]}" gradientUnits="userSpaceOnUse" x1="500" y1="420" x2="370" y2="140"><stop stop-color="{color}" stop-opacity=".98"/><stop offset=".85" stop-color="{color}" stop-opacity=".9"/><stop offset="1" stop-color="{color}" stop-opacity=".12"/></linearGradient>')
    svg.append('</defs><rect x="50" y="40" width="900" height="440" rx="3" fill="url(#floor-fill)"/>')
    for x,y,w,h,color in [(55,45,670,210,"#e6ece0"),(735,45,210,145,"#f5f0e2"),(55,265,260,210,"#f3f1e9"),(325,265,380,100,"#e9eee5"),(325,375,380,100,"#f2eade"),(715,205,230,270,"#eef0e7")]:
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>')
    svg.append('<ellipse cx="370" cy="140" rx="90" ry="62" fill="url(#dock-light)"/>')
    for i,route in enumerate(scene["routes"]):
        path = "M " + " L ".join(f"{x},{y}" for x,y in route["points"])
        label = html.escape(" → ".join(route["states"]))
        svg.append(f'<path class="route-guide" aria-hidden="true" d="{path}" fill="none" stroke="url(#fade-{route["id"]})" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" opacity=".45"/>')
        svg.append(f'<path id="route-{route["id"]}" class="route-track" data-states="{" ".join(route["states"])}" aria-label="Illustrative route {label}" d="{path}" fill="none" stroke="url(#fade-{route["id"]})" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" pathLength="1" style="--route-delay:{i * -.9}s"/>')
        svg.append(f'<g class="route-echo" aria-hidden="true" opacity="0"><ellipse rx="18" ry="11" fill="{route["color"]}" opacity=".45"/><image href="assets/illustrations/robot-marker-v3.png" x="-22" y="-24" width="44" height="48" opacity=".5"/><animateMotion dur="8s" begin="{-i*1.4}s" repeatCount="indefinite"><mpath href="#route-{route["id"]}"/></animateMotion><animate attributeName="opacity" values=".45;.4;.15;0" keyTimes="0;.6;.85;1" dur="8s" begin="{-i*1.4}s" repeatCount="indefinite"/></g>')
    for room,(x,y) in scene["room_labels"].items():
        svg.append(f'<text x="{x}" y="{y}" class="floor-room-label" text-anchor="middle">{room}</text>')
    svg.append('<g fill="none" stroke="#6f8273" stroke-width="9" stroke-linecap="square" filter="url(#wall-shadow)"><rect x="50" y="40" width="900" height="440" rx="2"/>')
    for xa,ya,xb,yb in scene["walls"]:
        svg.append(f'<path d="M{xa},{ya} L{xb},{yb}"/>')
    svg.append('</g>')
    svg.append('<g id="fixed-robot" data-room="C"><ellipse cx="500" cy="430" rx="31" ry="11" fill="#213931" opacity=".12"/><image href="assets/illustrations/robot-marker-v3.png" x="461" y="382" width="78" height="76"/><text x="500" y="505" class="floor-marker-label" text-anchor="middle">START · C</text></g>')
    svg.append('<g id="fixed-destination" data-room="F"><image href="assets/illustrations/dock-marker-v3.png" x="324" y="91" width="92" height="90"/><text x="370" y="203" class="floor-marker-label" text-anchor="middle">GOAL · F</text></g>')
    svg.append('</svg>')
    legend = ''.join(f'<span class="route-key"><i style="background:{route["color"]}"></i>{html.escape(route["label"])}</span>' for route in scene["routes"])
    return ''.join(svg) + f'<div class="route-legend">{legend}</div><button class="route-motion-button" id="route-motion" type="button" aria-pressed="false">Pause routes</button>'
