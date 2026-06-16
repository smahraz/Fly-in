The very first line must be italicized and read: This project has been created as part of the 42 curriculum by `smahraz`

## Description:
The objectives of this project are multiple, but the main focus is on path finding and synchronizing drones to achieve the most efficient movement, minimizing the number of turns as much as possible.

## Visualization:
- i used [raylib](https://www.raylib.com) for visualization.
- The visual representation provides an intuitive view of the environment, including zones, connections, and drone movements. It helps users better understand the pathfinding process, monitor drone synchronization, and analyze the efficiency of the generated routes.
![simple map 1](assets/s1.png)

![hard map](assets/s3.png)

![s2](assets/s2.gif)
map: `maps/hard/02_capacity_hell.txt`
## Instructions:
- to run:
```bash
make
```
or
```bash
make run
```
- for special map:
```bash
uv run python -m flyin <map_path>
```
##### Install dependencies:
```bash
uv sync
```
## Resources:
- [Dijkstra](https://en.wikipedia.org/wiki/Dijkstra's_algorithm)
- [dfs](https://www.youtube.com/watch?v=Urx87-NMm6c)
##### Use of AI:
- doc string

## Approach:
```mermaid
flowchart TD
    Start([Start])

    Find[Find all possible paths]
    Sort[Sort by cost then by priority]
    Graph[Convert paths to graph]

    Loop[Loop through all drones]
    Check[Check possible next zones]

    Free{Next zone free?}
    Cost{Cost to reach end <=<br/>min cost + drones in start_hub?}
    More{More possibilities left?}

    Move[Move drone]

    EndTurn[End turn]
    Reached{All drones<br/>reached end?}
    End([End])

    Start --> Find
    Find --> Sort
    Sort --> Graph
    Graph --> Loop

    Loop --> Check
    Check --> Free

    Free -->|Yes| Cost
    Free -->|No| More

    Cost -->|Yes| Move
    Cost -->|No| More

    Move --> EndTurn

    More -->|No| EndTurn
    More -->|Yes| Check

    EndTurn --> Reached

    Reached -->|No| Loop
    Reached -->|Yes| End
```

###### Graph:
- zone gives `dict` of possible next zones with cost.
- next possible zones are sorted by default (cost first, then priority).
```python
{
    Zone(start: 0.0,0.0): {
	    Zone(fast_junction: 150.0,0.0): 4,
	    Zone(slow_path1: 150.0,150.0): 5
	},
    Zone(fast_junction: 150.0,0.0): {
	    Zone(fast_path: 300.0,0.0): 3
	},
    Zone(fast_path: 300.0,0.0): {
	    Zone(merge_point: 450.0,0.0): 2
	},
    Zone(merge_point: 450.0,0.0): {
	    Zone(goal: 600.0,0.0): 1
	},
    Zone(slow_path1: 150.0,150.0): {
	    Zone(slow_path2: 300.0,150.0): 3
	},
    Zone(slow_path2: 300.0,150.0): {
	    Zone(merge_point: 450.0,0.0): 2
	}
}
```
