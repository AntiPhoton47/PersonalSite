---
title: "Mini-Explainers"
permalink: /explainers/
author_profile: false
toc: true
toc_sticky: true
code_example_runs:
  - slug: notebook-demo-explainer
    source: notebook_demo.ipynb
    title: Notebook explainer (small system)
    params:
      max_n: 5
---

This page is for short, visual explanations of ideas that recur across the site. The aim is not to be fully rigorous, but to give an accessible picture that makes the more technical material easier to enter.

## Discretizing a Continuous Signal

One recurring theme in computational physics is that smooth dynamics have to be represented in a discrete way before a machine can do anything with them. This toy example shows that move in a harmless setting: a simple sine wave sampled point by point.

{% include code-example.html slug="sine-wave-demo" description="A simple example of turning a smooth signal into a finite set of samples." %}

## Small Growth, Large Consequences

Another recurring idea in both physics and machine learning is that very simple rules can scale quickly enough to become computationally or conceptually important. This notebook uses the elementary sequence of squares as a stand-in for that broader lesson.

{% include code-example.html slug="notebook-demo-explainer" description="A tiny notebook-backed explainer about how quickly simple structures can grow." %}

## Why These Exist

These explainers are placeholders for a more serious library of notebook-backed essays. For now, they serve as a gentle bridge between plain-language summaries and the more technical research material elsewhere on the site.
