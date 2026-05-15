# ITL Component Quick Reference

One-page cheat sheet for all documentation components.

---

## 📦 Alerts

```liquid
{% include alert.html type="info|warning|success|danger" title="Optional Title" content="Message" %}
```

**Colors:** info (blue), warning (yellow), success (green), danger (red)

---

## 🏷️ Badges

```liquid
{% include badge.html text="v2.0.0" color="success|warning|danger|info|muted" size="small|medium|large" icon="✨" %}
```

---

## 🔘 Buttons

```liquid
{% include button.html text="Label" link="/url" style="primary|secondary|success|danger|outline" icon="🚀" size="small|medium|large" target="_blank" %}
```

---

## 📦 Cards

```liquid
{% include card.html 
   title="Title" 
   icon="🔒"
   description="Description text"
   link="/docs/page"
   tags="tag1,tag2,tag3"
   badge="v2.0.0"
   badge_color="success|warning|info"
%}
```

---

## 💻 Code Blocks

```liquid
{% capture code %}
your code here
{% endcapture %}
{% include code-block.html code=code language="bash|python|yaml|json|powershell" title="Optional Title" filename="file.py" %}
```

**Languages:** bash, python, yaml, json, powershell, javascript, typescript, csharp, bicep

---

## 🔗 Link Cards

```liquid
{% include link-card.html 
   title="Link Title" 
   description="Link description"
   link="/target"
   icon="🏗️"
   external="true|false"
%}
```

---

## 🗺️ Breadcrumbs

```liquid
{% include breadcrumb.html path="Home,Docs,Page" %}
```

---

## 📊 Grids

```liquid
{% capture content %}
  {% include card.html ... %}
  {% include card.html ... %}
{% endcapture %}
{% include grid.html content=content columns="1|2|3|4|auto" gap="small|medium|large" %}
```

---

## 🎨 Colors

| Variable | Hex | Usage |
|----------|-----|-------|
| `--bg` | `#0d1117` | Page background |
| `--surface` | `#161b22` | Card background |
| `--border` | `#30363d` | Borders |
| `--accent` | `#1f6feb` | Primary/Azure blue |
| `--accent2` | `#58a6ff` | Light blue |
| `--text` | `#e6edf3` | Primary text |
| `--muted` | `#8b949e` | Secondary text |
| `--success` | `#3fb950` | Green |
| `--warning` | `#d29922` | Orange/yellow |
| `--danger` | `#f85149` | Red |

---

## 📋 Common Patterns

### Callout

```liquid
{% include alert.html type="info" content="Important note" %}
```

### CTA Button

```liquid
{% include button.html text="Get Started" link="/docs" style="primary" icon="🚀" %}
```

### Feature Grid

```liquid
{% capture features %}
  {% include card.html title="Feature 1" icon="🔒" description="..." %}
  {% include card.html title="Feature 2" icon="🔔" description="..." %}
  {% include card.html title="Feature 3" icon="📊" description="..." %}
{% endcapture %}
{% include grid.html content=features columns="3" %}
```

### Installation Instructions

```liquid
{% capture install %}
git clone https://github.com/ITlusions/repo.git
cd repo
docker compose up -d
{% endcapture %}
{% include code-block.html code=install language="bash" title="Quick Start" %}
```

### Documentation Links

```liquid
{% include link-card.html 
   title="Documentation" 
   description="Full reference guide"
   link="/docs"
   icon="📖"
%}
```

---

## 🔗 Resources

- [Full Documentation](README.md)
- [Live Demo](COMPONENTS_DEMO.md)
- [Integration Guide](INTEGRATION.md)
- [ITL.Github Repository](https://github.com/ITlusions/ITL.Github)

---

**Quick Copy Template:**

```liquid
---
layout: default
title: Page Title
---

# Page Title

{% include breadcrumb.html path="Home,Section,Page" %}

{% include alert.html type="info" content="Important information" %}

## Section

{% capture code %}
command here
{% endcapture %}
{% include code-block.html code=code language="bash" %}

{% include button.html text="Action" link="/page" style="primary" %}
```
