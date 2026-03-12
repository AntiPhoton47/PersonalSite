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

## Email subscription
- Put your provider’s embed form (or a simple link) into: `_includes/email_subscribe.html`
- It is displayed on the home page and can be added elsewhere via:
  `{% include email_subscribe.html %}`

## Local preview (optional)
```bash
gem install bundler
bundle install
bundle exec jekyll serve
```
