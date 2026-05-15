# ITL Documentation Components

Central library of reusable Jekyll components for all ITLusions documentation sites.

## 📦 Available Components

| Component | Description | Use Case |
|-----------|-------------|----------|
| `alert.html` | Info/warning/success/danger alerts | Callouts, notices, warnings |
| `badge.html` | Status/version badges | Version tags, labels, categories |
| `button.html` | Styled action buttons | CTAs, navigation links |
| `card.html` | Feature cards with icons | Feature showcases, extension cards |
| `code-block.html` | Syntax-highlighted code with copy button | Code examples, installation commands |
| `breadcrumb.html` | Navigation breadcrumbs | Page navigation |
| `grid.html` | Responsive grid layouts | Card grids, multi-column layouts |
| `link-card.html` | Clickable documentation cards | Navigation, related links |

---

## 🚀 Quick Start

### In Your Repository

#### Option 1: Direct Include (Same Repo)

If your docs are in the **same repository**:

```liquid
{% include alert.html type="info" content="Your message here" %}
```

#### Option 2: Remote Include (Cross-Repo)

If your docs are in a **different repository**, include components via Git submodule or copy them:

**Method A: Git Submodule (Recommended)**

```bash
cd your-repo/docs
git submodule add https://github.com/ITlusions/ITL.Github.git _vendor/itl-github
ln -s _vendor/itl-github/docs/_includes _includes
```

**Method B: Copy Components**

```bash
# Copy to your repo
cp -r ITL.Github/docs/_includes/* your-repo/docs/_includes/
```

---

## 📖 Component Reference

### 1. Alert

Display informational, warning, success, or danger alerts.

```liquid
{% include alert.html type="info" title="Note" content="Your message here" %}
{% include alert.html type="warning" content="Warning message" %}
{% include alert.html type="success" title="Success!" content="Operation completed" %}
{% include alert.html type="danger" content="Critical issue" %}
```

**Parameters:**
- `type`: `info` | `warning` | `success` | `danger` (default: `info`)
- `title`: Optional heading text
- `content`: Alert message (required)
- `icon`: Optional custom icon (default: auto based on type)

---

### 2. Badge

Small status/version badges.

```liquid
{% include badge.html text="v2.0.0" color="success" %}
{% include badge.html text="Beta" color="warning" %}
{% include badge.html text="New" color="info" icon="✨" %}
```

**Parameters:**
- `text`: Badge text (required)
- `color`: `success` | `warning` | `danger` | `info` | `muted` (default: `info`)
- `icon`: Optional icon/emoji before text
- `size`: `small` | `medium` | `large` (default: `medium`)

---

### 3. Button

Styled action buttons.

```liquid
{% include button.html text="Get Started" link="/docs" style="primary" %}
{% include button.html text="GitHub" link="https://github.com/..." style="secondary" icon="🔗" target="_blank" %}
```

**Parameters:**
- `text`: Button label (required)
- `link`: URL (required)
- `style`: `primary` | `secondary` | `success` | `danger` | `outline` (default: `primary`)
- `icon`: Optional icon/emoji before text
- `target`: Optional link target (`_blank`, `_self`, etc.)
- `size`: `small` | `medium` | `large` (default: `medium`)

---

### 4. Card

Feature cards with icon, title, description, and tags.

```liquid
{% include card.html 
   title="Feature Name" 
   icon="🔒"
   description="Feature description text"
   link="/docs/feature"
   tags="tag1,tag2,tag3"
   badge="v2.0.0"
   badge_color="success"
%}
```

**Parameters:**
- `title`: Card heading (required)
- `icon`: Icon/emoji (optional)
- `description`: Card description text (required)
- `link`: Optional link URL
- `tags`: Comma-separated tags (optional)
- `badge`: Optional badge text (e.g., "v2.0.0", "New", "Beta")
- `badge_color`: `success` | `warning` | `info` (default: `info`)

---

### 5. Code Block

Syntax-highlighted code blocks with copy button.

```liquid
{% capture code %}
git clone https://github.com/ITlusions/repo.git
cd repo
docker compose up -d
{% endcapture %}
{% include code-block.html code=code language="bash" title="Installation" %}
```

**Parameters:**
- `code`: Code content (required)
- `language`: `bash` | `python` | `yaml` | `json` | `powershell` (default: `bash`)
- `title`: Optional code block title
- `filename`: Optional filename to display

**Supported Languages:**
- `bash` / `shell`
- `python`
- `yaml` / `yml`
- `json`
- `powershell` / `ps1`
- `javascript` / `js`
- `typescript` / `ts`
- `csharp` / `cs`
- `bicep`

---

### 6. Breadcrumb

Navigation breadcrumbs.

```liquid
{% include breadcrumb.html path="Home,Documentation,Architecture" %}
```

**Parameters:**
- `path`: Comma-separated breadcrumb items

---

### 7. Grid

Responsive grid layout for cards and other content.

```liquid
{% capture grid_content %}
  {% include card.html title="Card 1" description="..." %}
  {% include card.html title="Card 2" description="..." %}
  {% include card.html title="Card 3" description="..." %}
{% endcapture %}
{% include grid.html content=grid_content columns="3" gap="large" %}
```

**Parameters:**
- `content`: HTML content to wrap in grid (required)
- `columns`: `1` | `2` | `3` | `4` | `auto` (default: `3`)
- `gap`: `small` | `medium` | `large` (default: `medium`)

---

### 8. Link Card

Clickable card for documentation links.

```liquid
{% include link-card.html 
   title="Architecture Guide" 
   description="System design and technical architecture"
   link="/ARCHITECTURE"
   icon="🏗️"
%}
```

**Parameters:**
- `title`: Link title (required)
- `description`: Description text (required)
- `link`: Target URL (required)
- `icon`: Icon/emoji (optional)
- `external`: `true`/`false` - adds external link indicator (default: `false`)

---

## 🎨 Design System

All components follow the **ITL Design System** with Azure Portal dark theme:

### Color Palette

```css
--bg: #0d1117           /* Dark background */
--surface: #161b22      /* Card/panel background */
--surface2: #21262d     /* Hover/secondary surface */
--border: #30363d       /* Borders */
--accent: #1f6feb       /* Primary/Azure blue */
--accent2: #58a6ff      /* Light blue */
--text: #e6edf3         /* Primary text */
--muted: #8b949e        /* Muted text */
--success: #3fb950      /* Green */
--warning: #d29922      /* Yellow/orange */
--danger: #f85149       /* Red */
```

### Typography

- **Font**: `-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif`
- **Monospace**: `ui-monospace, "Cascadia Code", "SFMono-Regular", Consolas, monospace`

### Spacing Scale

- **Small**: `1rem` (16px)
- **Medium**: `1.5rem` (24px)
- **Large**: `2rem` (32px)

---

## 📝 Usage Examples

### Complete Page Example

```liquid
---
layout: default
title: Getting Started
---

# Getting Started

{% include breadcrumb.html path="Home,Documentation,Getting Started" %}

{% include alert.html 
   type="info" 
   title="Prerequisites" 
   content="Ensure Docker and Docker Compose are installed." 
%}

## Installation

{% capture install %}
git clone https://github.com/ITlusions/your-repo.git
cd your-repo
docker compose up -d
{% endcapture %}
{% include code-block.html code=install language="bash" title="Quick Start" %}

## Features

{% capture features %}
{% include card.html title="Feature 1" icon="🚀" description="Description 1" %}
{% include card.html title="Feature 2" icon="🔒" description="Description 2" %}
{% include card.html title="Feature 3" icon="📊" description="Description 3" %}
{% endcapture %}
{% include grid.html content=features columns="3" %}

<div style="margin-top: 3rem;">
{% include button.html text="View Documentation" link="/docs" style="primary" %}
{% include button.html text="GitHub" link="https://github.com/..." style="secondary" target="_blank" %}
</div>
```

---

## 🔄 Migration from Plain Markdown

### Before

```markdown
> **Note:** This is important

## Installation

\`\`\`bash
npm install
\`\`\`
```

### After

```liquid
{% include alert.html type="info" title="Note" content="This is important" %}

## Installation

{% capture code %}
npm install
{% endcapture %}
{% include code-block.html code=code language="bash" title="Install Dependencies" %}
```

---

## 🏗️ Repositories Using This Library

- [ITL.ControlPlane.Attestation](https://github.com/ITlusions/ITL.ControlPlane.Attestation)
- [ITL.BrainCell](https://github.com/ITlusions/ITL.BrainCell)
- [ITL.ControlPlane.CLI](https://github.com/ITlusions/ITL.ControlPlane.CLI)
- [ITL.Github](https://github.com/ITlusions/ITL.Github) (this repo)

---

## 🤝 Contributing

To add or improve components:

1. Edit files in `docs/_includes/`
2. Test locally with Jekyll: `bundle exec jekyll serve`
3. Update this documentation
4. Submit a PR to `ITL.Github`

---

## 📜 License

MIT License - See [LICENSE](../LICENSE)

---

## 🔗 Related

- [Component Demo](COMPONENTS_DEMO.md) - Live examples
- [Migration Guide](MIGRATION_GUIDE.md) - Refactoring existing docs
- [Jekyll Documentation](https://jekyllrb.com/docs/includes/)
