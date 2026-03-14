# Personal Academic Website + Blog (GitHub Pages + Jekyll + Minimal Mistakes)

This repo is a ready-to-deploy personal academic website with:
- Blog (posts in `_posts/`)
- RSS feed (via `jekyll-feed`)
- Dark mode (Minimal Mistakes skins; default set to `dark`)
- MathJax for LaTeX
- Pages: About, Research, Publications, Media, Contact
- Downloadable CV placeholder (`assets/files/CV.pdf`)
- BibTeX download (`assets/files/publications.bib`)
- Optional email subscription embed (MailerLite/ConvertKit placeholder include)

## Quick start (GitHub Pages)
1. Create a new GitHub repo named **<your-username>.github.io**
2. Upload this repo’s contents (or push via git).
3. In GitHub: **Settings → Pages**
   - Source: **GitHub Actions** (recommended; workflow included)
4. Edit `_config.yml`:
   - `url`, `title`, `author`, social links, etc.
5. Your site should appear at: `https://<your-username>.github.io`

## Custom domain
1. Buy a domain.
2. In GitHub: **Settings → Pages → Custom domain**, set it (e.g. `yourname.com`).
3. Set DNS:
   - Apex domain A records → GitHub Pages IPs
   - `www` CNAME → `<your-username>.github.io`
GitHub will show the exact records to add.

## Writing a blog post
Add a file like: `_posts/2026-02-17-my-first-post.md`

## Executable code + plots
- Put trusted Python scripts in `assets/code/`.
- You can also put Jupyter notebooks there as `.ipynb`.
- Run `python3 scripts/render_code_examples.py`.
- Embed the result in any page or post with:
  `{% include code-example.html slug="your-script-name" %}`
- The renderer executes scripts and notebooks, captures stdout/stderr, saves any Matplotlib or notebook image outputs into `assets/generated/code/`, and exposes notebook markdown cells in the rendered page.
- To create global named variants, define them in `_data/code_example_runs.yml` with `source`, `slug`, `title`, and `params`.
- To create page-local variants, add a `code_example_runs:` list to that page or post front matter with the same fields.

## Email subscription
- Configure your provider in `_config.yml` under `newsletter:`
- For EmailOctopus, paste the inline form script URL and form ID from the EmailOctopus form builder
- The site renders the form through `_includes/email_subscribe.html`
- It is displayed on the home page and can be added elsewhere via:
  `{% include email_subscribe.html %}`

## Blog email outbox
- EmailOctopus does not provide a clean native RSS-to-email flow for this site, so the repo prepares campaign content automatically instead.
- The workflow `.github/workflows/prepare-blog-emails.yml` watches `_posts/` changes on `main`.
- For each changed post it generates:
  - `newsletter_outbox/<post-slug>/campaign.html`
  - `newsletter_outbox/<post-slug>/campaign.txt`
  - `newsletter_outbox/<post-slug>/metadata.json`
- Those files are committed back automatically and are excluded from the public Jekyll site.
- In EmailOctopus, create a campaign and paste in the generated HTML or plain text.

## Local preview (optional)
```bash
gem install bundler
bundle install
python3 -m pip install -r requirements-tools.txt
python3 scripts/render_code_examples.py
bundle exec jekyll serve
```
