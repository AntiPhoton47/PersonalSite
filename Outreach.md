---
title: "Outreach"
permalink: /outreach/
---

I am the co-organizer of the public outreach events for the Briegel group at the University of Innsbruck, where our aim is to engage students of all ages with the research carried out in the group and the basic principles behind artificial intelligence. 

We recently finished putting together a booth consisting of four activities.

![](/assets/images/IMG_5850.jpeg)

Below I will explain in more detail about these activities. 

## Current Setup

### Interactive Reinforcement Learning Platform

We have an interactive reinforcement learning platform implementing the projective simulation algorithm (what is being projected on the main screen in the preceding image), where visitors can change the environment and the agent parameters in real time. The website can be found [here](https://jpazem.github.io/InteractiveRLlab/). The demo is designed to make reinforcement learning feel concrete: instead of speaking only in abstractions about “training” and “optimization”, students can watch an agent learn from trial and error in front of them and see how its behaviour changes when the learning dynamics are adjusted.

![](/assets/images/rl-lab-03-15-2026_08_29_PM.png?raw=true)

At the centre of the demo is a simple grid-world environment. The learner is the smiley face with the cowboy hat, and the aim is to reach the goal cell as efficiently as possible while avoiding bad regions such as lava and impassable walls. The platform is built around a sequence of challenge environments, beginning with a very simple open field and then moving to more structured scenarios such as a narrow corridor, a two-room layout with a key-door mechanic, and a maze-like challenge with dead ends and hazards. This progression is useful for outreach because it shows that reinforcement learning is not just about eventually getting a reward, but about discovering a good strategy under changing constraints.

The middle panel of the interface acts as a “memory inspector” or policy visualization. It displays arrows on the grid showing which actions the agent has learned to favour from each position; brighter arrows correspond to actions the agent is more likely to take. In other words, visitors can literally see a learned policy emerge rather than treating the agent as a black box. On the right, the reward plots show whether the learner is improving over time. When the agent has found a stable good strategy, the plotted rewards rise and then settle into a more consistently favourable pattern.

The educational point of the demo is not only that the agent can solve the task, but that projective simulation gives a particularly intuitive way to talk about how it learns. In this model, the agent’s memory is represented as a network of “clips” corresponding to experiences and actions, and decision-making is described as a random walk through that memory network. Rewards strengthen useful transitions, so students can connect the abstract idea of reinforcement learning to something more visual and mechanistic.

The sliders in the left column control the environment and reward structure. These include the simulation speed, the goal reward, the lava penalty, and the “step cost”, which is especially useful pedagogically because it makes clear why an agent might prefer a shorter path over a longer one. A more negative step cost penalizes wandering and pushes the learner toward efficient behaviour.

The sliders in the middle column control the agent parameters and let visitors explore how different learning strategies behave:

- Memory damping slider: determines how easily the agent remembers their past actions, with a high value indicating that the agent will quickly forget what they did in past episodes.
- Reward coupling slider: controls by what factor the agent feels the reward, with higher values magnifying the reward they receive.
- Glow decay slider: controls how strongly a recent rewarding path continues to influence future decisions, which is particularly important in environments with sparse rewards.
- Exploration slider: determines how often the agent ignores its current policy and takes a random action instead.
- Temperature parameter slider: introduces a softer kind of randomness by flattening the learned action preferences, so visitors can see the difference between deliberate exploration and noisy decision-making.

In practice, this makes the platform a nice bridge between school-level intuition and research-level ideas. Younger students can treat it as an interactive puzzle about getting a character to a goal, while older students can use it to talk about exploration, exploitation, policy formation, reward shaping, memory effects, and the advantages of interpretable learning models.

### Generating Quantum Circuits with Diffusion Models

A volunteer team from my group assembled an activity by combining a natural language image generation diffusion model (like the Midjourney model) and a privately trained diffusion model which generates quantum circuits from descriptions. The activity starts by prompting you to write a description of an image you want to see, and then it shows you how it generates this image from a noisy initial image. The program tries to teach you about using the same principles to create quantum circuit diagrams.

![](/assets/images/IMG_5852.jpeg)

### Modular Group Research Poster

We also have a research poster that explains the basic motivations of the group and recruits different concepts to explain some of the research projects undertaken in the group. Because the group I am part of is so diverse in its interests, we converted the traditional research poster into a modular poster that allows the presenters to switch out different research project cards and their associated concept cards to suit their different backgrounds or to accommodate their interests. Here is what it looks like:

![](/assets/images/76A27281-5F66-4584-9D59-27FFE9404D09_1_201_a.jpeg)

### Ask Me Anything!

We thought that some of the most useful information we can pass along to students is our personal experiences as scientists and our journey to get to that point. To this end, we created a simple set of cards with questions that the students can ask us, with the intention that the interaction is unique and tailored to the backgrounds of the scientists present at the time.

## Future Plans and Contact

We are always trying to improve our outreach ideas to reach broader audiences, so please do not hesitate to reach out to me if you have suggestions (my contact email is on every page of the website)! 

We also encourage the use of the reinforcement learning application as an educational tool. If you or are group you have organized are interested in visiting the university for a demonstration, please also contact me :)
