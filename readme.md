# Maze Image Solver

A tool that solves maze images using image preprocessing, skeletonization, and BFS.

## Description

This project preprocesses a maze image, extracts its skeleton, and applies Breadth-First Search (BFS) to quickly find the solution path.

## Features

- Image preprocessing to build up boundary so that the path won't go through outside the maze
- Skeletonization for path simplification
- BFS algorithm for fast pathfinding
- Visualization of the solved maze

## Demo

![Demo](demo_images/demo1.png)
![Demo](demo_images/demo2.png)

## How to Use

Follow these steps to solve a maze:

0. Execute **MazeApp.py**
1. Click **Open** to load a maze image.
2. Click **Set** to enable start and end point selection.
3. Click the left mouse button on the maze to mark the **start point**.
4. Click the left mouse button on the maze to mark the **end point**.
5. Click **Start** to run the solver and visualize the path.
6. Click **Reset** to clear the start and end points and try again.

# Techique

## Otsu

### 1.Histogram

$$
p(i) = \frac{\text{number of pixels with intensity } i }{N}, \quad i = 0, 1, \dots, 255
$$

where $N$ is the total number of pixels.

---

### 2. Try all possible thresholds $t$

**compute probabilities (weights)**

$$
\omega_0(t) = \sum_{i=0}^{t} p(i),
\quad
\omega_1(t) = \sum_{i=t+1}^{L-1} p(i)
$$

**compute means**

$$
\mu_0(t) = \frac{1}{\omega_0(t)} \sum_{i=0}^{t} i \cdot p(i),
\quad
\mu_1(t) = \frac{1}{\omega_1(t)} \sum_{i=t+1}^{L-1} i \cdot p(i)
$$

**compute variances**

$$
\sigma_b^2(t) = \omega_0(t)\,\omega_1(t)\,\big(\mu_0(t) - \mu_1(t)\big)^2
$$

---

### 3. Find the optimal threshold

$$
t^* = \underset{t}{\arg\max}\ \sigma_b^2(t)
$$

---

### 4. Apply the thresholding

$$
dst(x, y) =
\begin{cases}
255 & \text{if } I(x, y) > t^* \\
0   & \text{if } I(x, y) \leq t^*
\end{cases}
$$
