---
title: "Resources"
permalink: /resources/
code_example_runs:
  - slug: sine-wave-demo-high-frequency
    source: sine_wave_demo.py
    title: Sine wave demo (high frequency)
    params:
      amplitude: 0.8
      frequency: 2.5
      step: 0.04
  - slug: notebook-demo-wide
    source: notebook_demo.ipynb
    title: Notebook demo (wider range)
    params:
      max_n: 11
---

It's a big world out there, and there is so much to see and do, maybe a bit too much... While I will continue to be endlessly fascinated by our vast cosmos, it is sometimes difficult to know what events/initiatives are happening out there and where to look for resources. Luckily, I have compiled a list of current initiatives/institutions I am part of or am interested in, as well as links to courses and some research/course notes, and just general resources for those of you who want to get your feet wet in the theoretical physics aether. I hope you enjoy :)

## Starter Pack

The theoretical physicist Gerard 't Hooft already has a very informative and comprehensive guide to becoming a theoretical physicist on their [webpage](https://www.goodtheorist.science/index.html), but I will try to give my own perspective coming from a different background and with a more contemporary twist.

English is the lingua franca of physics and much of academia, so you have to make sure you have a working knowledge of it and that you can prove this to any institutions where you want to study. The basics of the language are quite simple and you can usually pick up what you need through ingesting media or talking to people; AI has evolved rapidly to the point where it can really help you practice the language (or any language for that matter) as well. My advice is to not worry too much about perfecting your grammar or pronunciation since English is very forgiving on both fronts, just make sure you can be understood. Of course, to become a good writer you will need to know the language better.

Theory breathes through the language of mathematics, so you absolutely must start with the basics. Calculus, linear algebra, and proofs are not decorative; they are the grammar of almost everything that comes later.

Some computer science knowledge is also handy to have, especially if you want to simulate models, test ideas numerically, or move anywhere near machine learning. You do not need to become a software engineer, but you should be able to make a computer do useful work for you. Getting familiar with languages such as Python or Julia is the best way to start since they are ubiquitous in physics and machine learning. Many theorists also like to use Wolfram Mathematica or Maple, which are very useful symbolic mathematics programs with their own syntax, but beware they are both proprietary software.

Most theorists would discombobulate at the mention of this, and in many respects it is not necessary to be able to actively work on theoretical physics, but I think it is important that every good theorist have some grounding in philosophy. Questions about explanation, evidence, abstraction, and what counts as understanding show up constantly even when people pretend they do not. You often find researchers - and arguably all people - have heavy philosophical commitments and understated assumptions that are fueling their argumentation and worldview; it helps to acknoweldge and convey these clearly, so knowing is half the battle here as usual.

Below I have listed some courses/subjects you should study - listed in order - to have a solid foundation.

## Courses

The Perimeter Institute of Theoretical Physics in Canada has a wonderful archive of all recorded talks and lectures given there called [PIRSA](https://pirsa.org/) which I urge you to take advantage of; they have material on almost any theoretical physics topic you can imagine. [MIT](www.youtube.com/@mitocw) and [Stanford](www.youtube.com/@stanfordonline) also post many of their excellent course lectures on YouTube, which I also recommend.

Mathematics Basics:
- Arithmetic / [link] | [notes] | [book]
- Algebra / [link] | [notes] | [book]
- Geometry / [link] | [notes] | [book]

Computer Science Basics:
- Introduction to Python/Julia / [link] | [notes] | [book]
- More Python/Julia / [link] | [notes] | [book]
- Introduction to Machine Learning / [link] | [notes] | [book]

Philosophy Basics:
- Introduction to Metaphysics / [link] | [notes] | [book]
- Introduction to Epistemology / [link] | [notes] | [book]
- Introduction to Philosophical Logic / [link] | [notes] | [book]

Introductory Mathematics:
- Proofs and Set Theory / [link] | [notes] | [book]
- Calculus I and II / [link] | [notes] | [book]
- Linear Algebra / [link] | [notes] | [book]
- Differential Equations I / [link] | [notes] | [book]
- Numerical Methods / [link] | [notes] | [book]

Introductory Physics:
- Classical Mechanics I / [link] | [notes] | [book]
- Electromagnetism I / [link] | [notes] | [book]
- Thermodynamics / [link] | [notes] | [book]

Intermediate Mathematics:
- Vector Calculus and Real Analysis / [link] | [notes] | [book]
- Probability Theory / [link] | [notes] | [book]
- Mathematical Methods / [link] | [notes] | [book]
- Differential Equations II / [link] | [notes] | [book]
- Linear Algebra II / [link] | [notes] | [book]

Intermediate Physics:
- Electromagnetism II / [link] | [notes] | [book]
- Optics / [link] | [notes] | [book]
- Quantum Theory I / [link] | [notes] | [book]
- Special Relativity / [link] | [notes] | [book]
- Classical Mechanics II / [link] | [notes] | [book]
- Statistical Physics I / [link] | [notes] | [book]

Advanced Mathematics:
- Differential Geometry / [link] | [notes] | [book]
- Topology / [link] | [notes] | [book]
- Complex Analysis / [link] | [notes] | [book]
- Functional Analysis / [link] | [notes] | [book]
- Measure Theory / [link] | [notes] | [book]
- Abstract Algebra and Group Theory / [link] | [notes] | [book]

Advanced Physics:
- Quantum Theory II / [link] | [notes] | [book] 
- Statistical Physics II / [link] | [notes] | [book]
- Quantum Information Theory / [link] | [notes] | [book]
- Advanced Electromagnetism / [link] | [notes] | [book]
- Solid State Physics / [link] | [notes] | [book]
- Nuclear Physics / [link] | [notes] | [book]
- Atomic and Molecular Physics / [link] | [notes] | [book]
- General Relativity I / [link] | [notes] | [book]

Graduate Physics:
- General Relativity II / [link] | [notes] | [book]
- Quantum Field Theory / [link] | [notes] | [book]
- Particle Physics / [link] | [notes] | [book]
- Relativistic Quantum Information / [link] | [notes] | [book]
- Quantum Foundations / [link] | [notes] | [book]

## Research Notes

Here I will list some useful research notes that are freely available. I also have some more basic [notes](/assets/files/resources/notes/My%20Notes.pdf) covering useful mathematical identities and basic properties plus physics unit conventions (but beware, it is a work in progress).



## Mini-Explainers

I am starting to build short notebook-backed explainers for recurring ideas on the site. They are meant to sit between plain-language summaries and the more technical research material.

- [Mini-Explainers](/explainers/) for short visual or computational explanations
- [Research](/research/) for the papers, talks, posters, and lay summaries
- [Posts](/posts/#explore-topics) for topic-based browsing through the blog

{% comment %}
## Computational Demos

The site can now render trusted Python code examples at build time, including generated plots and captured output. The block below is produced automatically from a script in `assets/code/`.

{% include code-example.html slug="sine-wave-demo" description="This demo is executed during the site build. The resulting figure and stdout are embedded directly into the page." %}

The same script can also be rendered with a different parameter set and embedded as a separate variant.

{% include code-example.html slug="sine-wave-demo-high-frequency" description="This is the same source file as the first demo, but executed with a different amplitude, frequency, and step size." %}

It also supports Jupyter notebooks, including markdown cells and notebook-generated outputs.

{% include code-example.html slug="notebook-demo" description="This notebook is executed during the site build. Its markdown text, plot, and printed output are rendered into the page." %}

Notebook runs can also be parameterized independently.

{% include code-example.html slug="notebook-demo-wide" description="This is the same notebook executed with a larger value range." %}
{% endcomment %}


## Current Initiatives and Institutions

Many of these initiatives/institutions/hubs are tailored towards my own interests so don't expect to find everything here.

### Initiatives

- [Without Spacetime](https://withoutspacetime.org/) (WOST)
- [Relativistic Quantum Information COST](https://rqi-cost.org/)
- [International Society for Relativistic Quantum Information](https://www.isrqi.net/)
- [BridgeQG](https://web.infn.it/BridgeQG/)
- [Centre for SpaceTime and the Quantum](https://www.cstq.org/)

### Institutions

- [Institute for Quantum Information and Quantum Optics Vienna](https://www.iqoqi-vienna.at/)
- [Perimeter Institute for Theoretical Physics](https://perimeterinstitute.ca/)
- [Nordic Institute for Theoretical Physics](https://nordita.org/)
- [Institute for Theoretical Physics ETH Zurich](https://itp.phys.ethz.ch/)
- [Max Planck Institute for Physics, Munich](https://www.mpp.mpg.de/en/)

### Hubs

- [Quantiki](https://quantiki.org/)

{% include site-crosslinks.html
  title="Keep Exploring"
  intro="If you came here for notes or demos, these are the fastest ways to branch into the rest of the site."
  links=site.data.resources_crosslinks %}
