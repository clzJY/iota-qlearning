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


def load_scene(case="original"):
    """Reuse one geometry; only the landmarks and legal alternatives change."""
    scene = json.loads((ROOT / "configs/floorplan.json").read_text())
    variants = scene.pop("variants", {})
    if case != "original":
        scene.update(variants[case])
    return scene


def route_scene(graph, case="original"):
    scene = load_scene(case)
    validate_scene(graph, scene)
    # Namespace every reference so multiple inline figures animate independently.
    prefix = "" if case == "original" else f"{case}-"
    def ident(name):
        return prefix + name
    def paint(name):
        return f"url(#{ident(name)})"
    sx,sy = scene["robot"]
    gx,gy = scene["destination"]
    start,goal = scene["start"],scene["goal"]
    choices = "; ".join(" → ".join(route["states"]) for route in scene["routes"])
    doors = ", ".join("–".join(edge) for edge in sorted(graph_edges(graph)))
    svg = [f'<svg id="{ident("route-scene")}" class="route-scene" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 540" role="img" aria-labelledby="{ident("scene-title")} {ident("scene-description")}">',
           f'<title id="{ident("scene-title")}">Three possible routes from {start} to {goal} through the corrected room map</title>',
           f'<desc id="{ident("scene-description")}">The robot stays in {start} and the dock stays in {goal}. Doorways connect {doors}. Coloured paths show {choices}. Translucent moving echoes fade at the destination. The routes illustrate legal choices, not recorded runs.</desc>',
           f'<defs><filter id="{ident("wall-shadow")}" x="-15%" y="-15%" width="140%" height="150%"><feDropShadow dx="0" dy="5" stdDeviation="3" flood-color="#59685e" flood-opacity=".17"/></filter>',
           f'<radialGradient id="{ident("dock-light")}"><stop stop-color="#dbaa56" stop-opacity=".27"/><stop offset="1" stop-color="#dbaa56" stop-opacity="0"/></radialGradient>',
           f'<linearGradient id="{ident("floor-fill")}" x2="0" y2="1"><stop stop-color="#f2f0e7"/><stop offset="1" stop-color="#e9e9de"/></linearGradient>']
    for route in scene["routes"]:
        color = route["color"]
        svg.append(f'<linearGradient id="{ident("fade-"+route["id"])}" gradientUnits="userSpaceOnUse" x1="{sx}" y1="{sy}" x2="{gx}" y2="{gy}"><stop stop-color="{color}" stop-opacity=".98"/><stop offset=".85" stop-color="{color}" stop-opacity=".9"/><stop offset="1" stop-color="{color}" stop-opacity=".12"/></linearGradient>')
    svg.append(f'</defs><rect x="50" y="40" width="900" height="440" rx="3" fill="{paint("floor-fill")}"/>')
    for x,y,w,h,color in [(55,45,670,210,"#e6ece0"),(735,45,210,145,"#f5f0e2"),(55,265,260,210,"#f3f1e9"),(325,265,380,100,"#e9eee5"),(325,375,380,100,"#f2eade"),(715,205,230,270,"#eef0e7")]:
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>')
    svg.append(f'<ellipse cx="{gx}" cy="{gy}" rx="90" ry="62" fill="{paint("dock-light")}"/>')
    for i,route in enumerate(scene["routes"]):
        path = "M " + " L ".join(f"{x},{y}" for x,y in route["points"])
        label = html.escape(" → ".join(route["states"]))
        stroke = paint("fade-"+route["id"])
        route_id = ident("route-"+route["id"])
        svg.append(f'<path class="route-guide" aria-hidden="true" d="{path}" fill="none" stroke="{stroke}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" opacity=".45"/>')
        svg.append(f'<path id="{route_id}" class="route-track" data-states="{" ".join(route["states"])}" aria-label="Illustrative route {label}" d="{path}" fill="none" stroke="{stroke}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" pathLength="1" style="--route-delay:{i * -.9}s"/>')
        svg.append(f'<g class="route-echo" aria-hidden="true" opacity="0"><ellipse rx="18" ry="11" fill="{route["color"]}" opacity=".45"/><image href="assets/illustrations/robot-marker-v3.png" x="-22" y="-24" width="44" height="48" opacity=".5"/><animateMotion dur="8s" begin="{-i*1.4}s" repeatCount="indefinite"><mpath href="#{route_id}"/></animateMotion><animate attributeName="opacity" values=".45;.4;.15;0" keyTimes="0;.6;.85;1" dur="8s" begin="{-i*1.4}s" repeatCount="indefinite"/></g>')
    for room,(x,y) in scene["room_labels"].items():
        svg.append(f'<text x="{x}" y="{y}" class="floor-room-label" text-anchor="middle">{room}</text>')
    svg.append(f'<g fill="none" stroke="#6f8273" stroke-width="9" stroke-linecap="square" filter="{paint("wall-shadow")}"><rect x="50" y="40" width="900" height="440" rx="2"/>')
    for xa,ya,xb,yb in scene["walls"]:
        svg.append(f'<path d="M{xa},{ya} L{xb},{yb}"/>')
    svg.append('</g>')
    rx,ry = scene["robot_label"]
    dx,dy = scene["destination_label"]
    svg.append(f'<g id="{ident("fixed-robot")}" data-room="{start}"><ellipse cx="{sx}" cy="{sy+10}" rx="31" ry="11" fill="#213931" opacity=".12"/><image href="assets/illustrations/robot-marker-v3.png" x="{sx-39}" y="{sy-38}" width="78" height="76"/><text x="{rx}" y="{ry}" class="floor-marker-label" text-anchor="middle">START · {start}</text></g>')
    svg.append(f'<g id="{ident("fixed-destination")}" data-room="{goal}"><image href="assets/illustrations/dock-marker-v3.png" x="{gx-46}" y="{gy-49}" width="92" height="90"/><text x="{dx}" y="{dy}" class="floor-marker-label" text-anchor="middle">GOAL · {goal}</text></g>')
    svg.append('</svg>')
    legend = ''.join(f'<span class="route-key"><i style="background:{route["color"]}"></i>{html.escape(route["label"])}</span>' for route in scene["routes"])
    return ''.join(svg) + f'<div class="route-legend">{legend}</div><button class="route-motion-button" id="{ident("route-motion")}" type="button" aria-controls="{ident("route-scene")}" aria-pressed="false">Pause routes</button>'
