---
layout: default
title: Component Demo
---

# ITL Component Library — Demo

Live examples of all reusable documentation components.

{% include breadcrumb.html path="Home,Components,Demo" %}

---

## 🎨 Alerts

{% include alert.html type="info" title="Information" content="This is an informational alert. Use it to highlight important details without blocking user flow." %}

{% include alert.html type="warning" content="This is a warning alert without a title. Use for caution messages." %}

{% include alert.html type="success" title="Success!" content="Your operation completed successfully. Everything is working as expected." %}

{% include alert.html type="danger" title="Critical Error" content="This is a critical error that requires immediate attention." %}

---

## 🔘 Buttons

### Styles

<div style="display: flex; gap: 1rem; flex-wrap: wrap; margin: 2rem 0;">
{% include button.html text="Primary" link="#" style="primary" %}
{% include button.html text="Secondary" link="#" style="secondary" %}
{% include button.html text="Success" link="#" style="success" %}
{% include button.html text="Danger" link="#" style="danger" %}
{% include button.html text="Outline" link="#" style="outline" %}
</div>

### Sizes

<div style="display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; margin: 2rem 0;">
{% include button.html text="Small" link="#" style="primary" size="small" %}
{% include button.html text="Medium" link="#" style="primary" size="medium" %}
{% include button.html text="Large" link="#" style="primary" size="large" %}
</div>

### With Icons

<div style="display: flex; gap: 1rem; flex-wrap: wrap; margin: 2rem 0;">
{% include button.html text="Rocket Launch" link="#" style="primary" icon="🚀" %}
{% include button.html text="GitHub" link="https://github.com/ITlusions" style="secondary" icon="🔗" target="_blank" %}
{% include button.html text="Documentation" link="/README" style="outline" icon="📖" %}
</div>

---

## 🏷️ Badges

### Colors

<div style="display: flex; gap: 0.75rem; flex-wrap: wrap; margin: 2rem 0;">
{% include badge.html text="v2.0.0" color="success" %}
{% include badge.html text="Beta" color="warning" %}
{% include badge.html text="Deprecated" color="danger" %}
{% include badge.html text="New Feature" color="info" icon="✨" %}
{% include badge.html text="Stable" color="muted" %}
</div>

### Sizes

<div style="display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: center; margin: 2rem 0;">
{% include badge.html text="Small" color="info" size="small" %}
{% include badge.html text="Medium" color="info" size="medium" %}
{% include badge.html text="Large" color="info" size="large" %}
</div>

---

## 📦 Cards

{% capture cards %}
{% include card.html 
   title="GitHub Actions" 
   icon="⚙️"
   description="Reusable workflows for CI/CD pipelines. Automated versioning, Docker builds, and PyPI publishing."
   link="/workflows"
   tags="CI/CD,automation,workflows"
   badge="Production"
   badge_color="success"
%}

{% include card.html 
   title="Composite Actions" 
   icon="🧩"
   description="Modular action building blocks. Python environment setup, release type detection, and more."
   link="/actions"
   tags="actions,reusable,composable"
   badge="Stable"
   badge_color="info"
%}

{% include card.html 
   title="Documentation" 
   icon="📚"
   description="Component library for Jekyll-based documentation sites. Consistent design across all ITL projects."
   link="/docs/_includes"
   tags="docs,jekyll,components"
   badge="New"
   badge_color="warning"
%}
{% endcapture %}
{% include grid.html content=cards columns="3" gap="large" %}

---

## 🔗 Link Cards

{% include link-card.html 
   title="Workflow Documentation" 
   description="Complete reference for all reusable GitHub Actions workflows"
   link="/workflows"
   icon="📖"
%}

{% include link-card.html 
   title="Getting Started Guide" 
   description="Quick start guide for integrating ITL workflows into your repository"
   link="/getting-started"
   icon="🚀"
%}

{% include link-card.html 
   title="GitHub Repository" 
   description="Source code, issues, and contributions"
   link="https://github.com/ITlusions/ITL.Github"
   icon="🔗"
   external="true"
%}

---

## 💻 Code Blocks

### Bash Example

{% capture bash_code %}
# Clone repository
git clone https://github.com/ITlusions/ITL.Github.git
cd ITL.Github

# Install dependencies
npm install

# View documentation locally
bundle exec jekyll serve
{% endcapture %}
{% include code-block.html code=bash_code language="bash" title="Installation" %}

### Python Example

{% capture python_code %}
from pathlib import Path

def discover_workflows(path: Path) -> list[str]:
    """Discover all reusable workflows."""
    return [
        f.stem for f in path.glob("_reusable-*.yml")
        if f.is_file()
    ]
{% endcapture %}
{% include code-block.html code=python_code language="python" filename="discover.py" %}

### YAML Example

{% capture yaml_code %}
name: CI Pipeline
on: [push, pull_request]

jobs:
  build:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-ci-python.yml@main
    with:
      python-version: "3.12"
{% endcapture %}
{% include code-block.html code=yaml_code language="yaml" filename=".github/workflows/ci.yml" %}

---

## 📊 Grid Layouts

### 2-Column Grid

{% capture two_col %}
{% include card.html title="Left Column" icon="📄" description="First column with equal width distribution for balanced layouts" %}
{% include card.html title="Right Column" icon="📄" description="Second column content with automatic responsive behavior" %}
{% endcapture %}
{% include grid.html content=two_col columns="2" gap="medium" %}

### 4-Column Grid

{% capture four_col %}
{% include card.html title="Step 1" icon="1️⃣" description="Clone repository" %}
{% include card.html title="Step 2" icon="2️⃣" description="Install dependencies" %}
{% include card.html title="Step 3" icon="3️⃣" description="Configure settings" %}
{% include card.html title="Step 4" icon="4️⃣" description="Deploy to production" %}
{% endcapture %}
{% include grid.html content=four_col columns="4" gap="small" %}

---

## 🎯 Combining Components

Rich layouts by nesting components:

{% include alert.html type="info" title="Quick Integration Guide" content="Follow these steps to add ITL workflows to your repository." %}

{% capture step1 %}
# Add workflow file
mkdir -p .github/workflows
touch .github/workflows/ci.yml
{% endcapture %}
{% include code-block.html code=step1 language="bash" title="Step 1: Create Workflow Directory" %}

{% capture step2 %}
name: CI
on: [push]
jobs:
  build:
    uses: ITlusions/ITL.Github/.github/workflows/_reusable-ci-python.yml@main
{% endcapture %}
{% include code-block.html code=step2 language="yaml" title="Step 2: Configure Workflow" %}

<div style="margin-top: 2rem;">
{% include button.html text="View Full Documentation" link="/README" style="primary" icon="📖" %}
{% include button.html text="Browse Workflows" link="/workflows" style="secondary" icon="⚙️" %}
</div>

---

## 📚 Documentation

- {% include badge.html text="README.md" color="info" %} Component API documentation
- {% include badge.html text="MIGRATION_GUIDE.md" color="warning" %} Refactoring guide
- {% include badge.html text="GitHub" color="muted" %} [Source code](https://github.com/ITlusions/ITL.Github)
