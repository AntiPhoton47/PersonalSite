---
title: "Outreach"
permalink: /outreach/
---

I am the co-organizer of the public outreach events for the Briegel group at the University of Innsbruck, where our aim is to engage students of all ages with the research carried out in the group and the basic principles behind artificial intelligence. 

## Interactive Reinforcement Learning Platform

We have an interactive reinforcement learning platform implementing the projective simulation algorithm, where you can augment the parameters of the agent and change the environment in real-time. The website can be found [here](https://jpazem.github.io/InteractiveRLlab/).

[The Demo](/assets/images/rl-lab-02-24-2026_08_19_PM.png?raw=true)

The goal of the demo is to get the agent (black dot) to reach the goal cell in the smallest number of steps consistent with the grid world, which will show up in the middle column of the interface as bright arrows along a certain path that the agent always follows, and on the rightmost column in the reward plots as increasing lines (or flat with relatively large values).

The sliders in the far left column control the environment parameters and all but the "step cost" slider are self-explanatory. The "step cost" slider allows you to add a penalty to the reward the agent sees per episode to encourage them to take less steps. The sliders in the middle column control the agent parameters.

- Memory damping slider: determines how easily the agent remembers their past actions, with a high value indicating that the agent will quickly forget what they did in past episodes.
- Reward coupling slider: controls by what factor the agent feels the reward, with higher values magnifying the reward they receive.
- Glow decay slider: controls the strength of past rewards, so a small value means that all past rewards have equal strength.
- Exploration and Temperature parameter sliders: determine how often the agent will act based on what they learned versus randomly, with larger values of each representing more random movements. The difference between the two is that "exploration" is based on a probability to use what they learned or act randomly, whereas "temperature parameter" just temporarily scrambles what they learned into noise if it is large.
