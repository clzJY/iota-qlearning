"""Tabular, episodic Q-learning. Actions name adjacent destination states.

The learner samples transitions. The independent shortest-path oracle below is
used only to diagnose learning, never to select training actions or update Q.
"""
from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass
class RoomWorld:
    graph: dict
    goal: str
    goal_reward: float = 1.0
    step_reward: float = 0.0

    def __post_init__(self):
        self.states = tuple(sorted(self.graph))
        if not self.states or self.goal not in self.states:
            raise ValueError("A nonempty graph and a valid goal are required")
        self.index = {state: i for i, state in enumerate(self.states)}
        self.goal_index = self.index[self.goal]
        self.actions = []
        for state in self.states:
            neighbors = self.graph[state]
            if not neighbors or len(set(neighbors)) != len(neighbors):
                raise ValueError("Every state needs distinct neighbors")
            if any(n not in self.index for n in neighbors):
                raise ValueError("Unknown destination state")
            for n in neighbors:
                if state not in self.graph[n]:
                    raise ValueError("This room-world model requires undirected edges")
            destinations = [] if state == self.goal else sorted(neighbors)
            self.actions.append(np.array([self.index[n] for n in destinations], dtype=int))
        self.mask = np.zeros((len(self.states), len(self.states)), dtype=bool)
        for s, actions in enumerate(self.actions):
            self.mask[s, actions] = True
        # Also checks that every state can reach the goal.
        self.distances()

    def distances(self):
        distance = {self.goal: 0}
        queue = deque([self.goal])
        while queue:
            current = queue.popleft()
            for neighbor in self.graph[current]:
                if neighbor not in distance:
                    distance[neighbor] = distance[current] + 1
                    queue.append(neighbor)
        if len(distance) != len(self.states):
            raise ValueError("Every room must be able to reach the goal")
        return distance

    def step(self, state, action):
        if not self.mask[state, action]:
            raise ValueError("Illegal action or action from a terminal state")
        terminal = action == self.goal_index
        return action, self.goal_reward if terminal else self.step_reward, terminal


def choose_action(q, state, actions, epsilon, rng):
    """Uniform exploration and uniform tie-breaking, restricted to legal actions."""
    if len(actions) == 0:
        raise ValueError("Terminal states have no actions")
    if rng.random() < epsilon:
        return int(rng.choice(actions))
    values = q[state, actions]
    best = actions[values == values.max()]
    return int(rng.choice(best))


def update(q, state, action, reward, next_state, terminal, next_actions, alpha, gamma):
    # Time-limit truncation is not terminal: callers must pass actual goal entry.
    target = reward if terminal else reward + gamma * float(q[next_state, next_actions].max())
    old = q[state, action]
    q[state, action] += alpha * (target - old)
    return float(target)


def reference_q(world, gamma):
    """Exact oracle for the declared zero-step-reward, positive-goal-reward model.

    If the chosen action enters a room d edges from the goal, the terminal reward
    arrives after d more actions: Q*(s,a) = reward * gamma**d.
    """
    if world.step_reward != 0 or world.goal_reward <= 0:
        raise ValueError("Shortest-path oracle requires zero step and positive goal rewards")
    distance = world.distances()
    q = np.zeros(world.mask.shape)
    for s, actions in enumerate(world.actions):
        for a in actions:
            q[s, a] = world.goal_reward * gamma ** distance[world.states[a]]
    return q


def bellman_residual(world, q, gamma):
    residual = 0.0
    for s, actions in enumerate(world.actions):
        for a in actions:
            nxt, reward, terminal = world.step(s, int(a))
            target = reward if terminal else reward + gamma * float(q[nxt, world.actions[nxt]].max())
            residual = max(residual, abs(target - q[s, a]))
    return float(residual)


def greedy_path(world, q, start, max_steps=100):
    """Deterministic evaluation: alphabetically first action among exact ties.

    Training uses random tie-breaking; evaluation consumes no training RNG.
    """
    state = world.index[start]
    path = [start]
    for _ in range(max_steps):
        if state == world.goal_index:
            return path, True
        actions = world.actions[state]
        state = int(actions[np.argmax(q[state, actions])])
        path.append(world.states[state])
    return path, state == world.goal_index


def train(world, start, settings, seed):
    episodes, max_steps = settings["episodes"], settings["max_steps"]
    alpha, gamma, epsilon = (settings[k] for k in ("alpha", "gamma", "epsilon"))
    if start not in world.index or episodes < 1 or max_steps < 1:
        raise ValueError("Invalid start or training budget")
    if not (0 < alpha <= 1 and 0 <= gamma < 1 and 0 <= epsilon <= 1):
        raise ValueError("Invalid learning parameters")
    rng = np.random.default_rng(seed)
    q = np.zeros(world.mask.shape)
    initial = q.copy()
    visits = np.zeros(world.mask.shape, dtype=int)
    oracle = reference_q(world, gamma)
    trace, snapshots = [], {0: q.copy()}
    total_steps = 0

    def record(episode, steps, reward, terminal, truncated, delta):
        counts = visits[world.mask]
        trace.append({
            "episode": episode, "steps": steps, "return": reward,
            "terminated": int(terminal), "truncated": int(truncated),
            "total_steps": total_steps, "delta_q": float(delta),
            "max_abs_error": float(np.abs(q - oracle)[world.mask].max()),
            "bellman_residual": bellman_residual(world, q, gamma),
            "min_visits": int(counts.min()), "unvisited_pairs": int((counts == 0).sum()),
            "start_value": float(q[world.index[start], world.actions[world.index[start]]].max()) if start != world.goal else 0.0,
        })

    record(0, 0, 0, start == world.goal, False, 0)
    for episode in range(1, episodes + 1):
        before = q.copy()
        state = world.index[start]
        terminal = state == world.goal_index
        total_reward, steps = 0.0, 0
        while not terminal and steps < max_steps:
            action = choose_action(q, state, world.actions[state], epsilon, rng)
            nxt, reward, terminal = world.step(state, action)
            update(q, state, action, reward, nxt, terminal, world.actions[nxt], alpha, gamma)
            visits[state, action] += 1
            steps += 1
            total_steps += 1
            total_reward += reward
            state = nxt
        record(episode, steps, total_reward, terminal, not terminal, np.abs(q - before)[world.mask].max())
        if episode in {1, 10, 50, 100, 300, 1000, episodes}:
            snapshots[episode] = q.copy()
    return {"initial": initial, "q": q, "visits": visits, "trace": trace, "snapshots": snapshots}


def sustained_threshold_episode(trace, key, threshold, window):
    """First below-threshold suffix of at least window episodes through run end.

    Episode zero is initialization and is never counted as a training observation.
    A later excursion resets the suffix, avoiding a misleading first-crossing claim.
    """
    last_failure = max((r["episode"] for r in trace if r["episode"] > 0 and r[key] >= threshold), default=0)
    if trace[-1]["episode"] - last_failure < window:
        return None
    return last_failure + 1
