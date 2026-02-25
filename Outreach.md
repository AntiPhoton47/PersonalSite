---
title: "Outreach"
permalink: /outreach/
---

I am the co-organizer of the public outreach events for the Briegel group at the University of Innsbruck, where our aim is to engage students of all ages with the research carried out in the group and the basic principles behind artificial intelligence. 

We recently finished putting together a booth consisting of four activities.

![](/assets/images/IMG_5850.jpeg)

## Interactive Reinforcement Learning Platform

We have an interactive reinforcement learning platform implementing the projective simulation algorithm (what is being projected on the main screen in the preceding image), where you can augment the parameters of the agent and change the environment in real-time. The website can be found [here](https://jpazem.github.io/InteractiveRLlab/).

![](/assets/images/rl-lab-02-24-2026_08_19_PM.png?raw=true)

The goal of the demo is to get the agent (black dot) to reach the goal cell in the smallest number of steps consistent with the grid world, which will show up in the middle column of the interface as bright arrows along a certain path that the agent always follows, and on the rightmost column in the reward plots as increasing lines (or flat with relatively large values).

The sliders in the far left column control the environment parameters and all but the "step cost" slider are self-explanatory. The "step cost" slider allows you to add a penalty to the reward the agent sees per episode to encourage them to take less steps. The sliders in the middle column control the agent parameters.

- Memory damping slider: determines how easily the agent remembers their past actions, with a high value indicating that the agent will quickly forget what they did in past episodes.
- Reward coupling slider: controls by what factor the agent feels the reward, with higher values magnifying the reward they receive.
- Glow decay slider: controls the strength of past rewards, so a small value means that all past rewards have equal strength.
- Exploration and Temperature parameter sliders: determine how often the agent will act based on what they learned versus randomly, with larger values of each representing more random movements. The difference between the two is that "exploration" is based on a probability to use what they learned or act randomly, whereas "temperature parameter" just temporarily scrambles what they learned into noise if it is large.

## Generating Quantum Circuits with Diffusion Models

A volunteer team from my group assembled an activity by combining a natural language image generation diffusion model (like the Midjourney model) and a privately trained diffusion model which generates quantum circuits from descriptions. The activity starts by prompting you to write a description of an image you want to see, and then it shows you how it generates this image from a noisy initial image. The program tries to teach you about using the same principles to create quantum circuit diagrams.

![](/assets/images/IMG_5852.jpeg)

## Modular Group Research Poster

We also have a research poster that explains the basic motivations of the group and recruits different concepts to explain some of the research projects undertaken in the group. Because the group I am part of is so diverse in its interests, we converted the traditional research poster into a modular poster that allows the presenters to switch out different research project cards and their associated concept cards to suit their different backgrounds or to accommodate their interests. Here is what it looks like:

![](/assets/images/76A27281-5F66-4584-9D59-27FFE9404D09_1_201_a.jpeg)

## Ask Me Anything!

We thought that some of the most useful information we can pass along to students is our personal experiences as scientists and our journey to get to that point. To this end, we created a simple set of cards with questions that the students can ask us, with the intention that the interaction is unique and tailored to the backgrounds of the scientists present at the time.
