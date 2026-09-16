"""Seed the munnakampala aggregator with sections, sample headlines and story pages.

Run with:
    python manage.py shell -c "exec(open('seed.py').read())"
"""
import urllib.request
from io import BytesIO

from django.core.files.images import ImageFile
from django.utils.lorem_ipsum import paragraphs
from PIL import Image as PILImage
from wagtail.images.models import Image
from wagtail.models import Page, Site

from links.models import Headline, HomePage, Section

# 1. Remove Wagtail's default "Welcome" page (slug 'home') and its Site.
welcome = Page.objects.filter(slug="home", depth=2).not_type(HomePage).first()
if welcome is not None:
    welcome.delete()  # cascades to the default Site
    print("Removed default welcome page")

# 2. Create the homepage at root.
root = Page.get_first_root_node()
home = HomePage.objects.first()
if home is None:
    home = HomePage(title="Home", slug="home")
    root.add_child(instance=home)
    home.save_revision().publish()
    print("Created homepage")

# 3. (Re)create the default Site pointing at the homepage.
site = Site.objects.filter(is_default_site=True).first()
if site is None:
    site = Site.objects.create(
        hostname="localhost",
        root_page=home,
        is_default_site=True,
    )
else:
    site.root_page = home
site.site_name = "munnakampala"
site.save()
print(f"Site: {site.site_name}")

# 4. Sections (columns).
section_specs = [
    # (name, sort_order, column)
    ("TOP STORIES", 0, 1),
    ("NATIONAL", 1, 1),
    ("SOCIETY", 2, 1),
    ("POLITICS", 3, 2),
    ("SPORTS & ENTERTAINMENT", 4, 2),
    ("ENTERTAINMENT", 5, 3),
]
Section.objects.exclude(name__in=[s[0] for s in section_specs]).delete()
sections = {}
for name, order, column in section_specs:
    sections[name], _ = Section.objects.update_or_create(
        name=name, defaults={"sort_order": order, "column": column}
    )

# 5. Sample headlines: (section, title, url, flag).
# Uganda-only, no Daily Monitor: real headlines from Ugandan outlets' RSS feeds, 12 Sep 2026.
sample = [
    ("TOP STORIES", "King Oyo buried as Omusuuga reaffirms new monarch", "https://observer.ug/news/king-oyo-buried-as-omusuuga-reaffirms-new-monarch/", ""),
    ("TOP STORIES", "Museveni asks Tooro to use legal means to resolve King Oyo succession dispute", "https://pmldaily.com/news/2026/09/museveni-asks-tooro-to-use-legal-means-to-resolve-king-oyo-succession-dispute.html", "red"),
    ("TOP STORIES", "Uganda's first oil delayed yet again, new target pushed to June 2027", "https://observer.ug/business/ugandas-first-oil-delayed-yet-again-new-target-pushed-to-june-2027/", ""),
    ("NATIONAL", "Museveni orders review of plan to turn Kampala City Square into hotel", "https://observer.ug/news/museveni-orders-review-of-plan-to-turn-kampala-city-square-into-hotel/", ""),
    ("NATIONAL", "Northern Bypass has nine of Kampala's 10 major crash hotspots", "https://www.independent.co.ug/northern-bypass-has-nine-of-kampalas-10-major-crash-hotspots/", ""),
    ("NATIONAL", "'God has remembered us': Gomba celebrates lifeline rain after five-month dry spell", "https://nilepost.co.ug/news/370464/god-has-remembered-us-gomba-celebrates-lifeline-rain-after-five-month-dry-spell", "green"),
    ("SOCIETY", "Ageing Soroti Hospital needs urgent replacement", "https://www.independent.co.ug/ageing-soroti-hospital-needs-urgent-replacement/", ""),
    ("SOCIETY", "EXPERTS: Uganda's education export boom built without a strategy", "https://www.independent.co.ug/experts-ugandas-education-export-boom-built-without-a-strategy/", ""),
    ("SOCIETY", "Uganda ranks fifth globally for entry openness as passport mobility score stands at 70", "https://www.watchdoguganda.com/news/20260912/197967/uganda-ranks-fifth-globally-for-entry-openness-as-passport-mobility-score-stands-at-70.html", ""),
    ("POLITICS", "100 judicial officers deployed to hear 346 election petitions", "https://pmldaily.com/news/2026/09/100-judicial-officers-deployed-to-hear-346-election-petitions.html", ""),
    ("POLITICS", "Ssenyonyi warns against giving away City Square, recalls controversial land deals", "https://pmldaily.com/news/2026/09/ssenyonyi-warns-against-giving-away-city-square-recalls-controversial-land-deals.html", "red"),
    ("POLITICS", "Journalists walk out on police over blockade at Tooro palace", "https://observer.ug/news/journalists-walk-out-on-police-over-blockade-at-tooro-palace/", ""),
    ("SPORTS & ENTERTAINMENT", "Masaza Cup Quarter-Finals Kick Off as Eight Counties Chase Semi-Final Berths", "https://nilepost.co.ug/sports/370430/masaza-cup-quarter-finals-kick-off-as-eight-counties-chase-semi-final-berths", ""),
    ("SPORTS & ENTERTAINMENT", "Grace Nakimera wows fans at 'The Power of Grace Charity Concert'", "https://mbu.ug/2026/09/12/grace-nakimera-wows-fans-at-the-power-of-grace-charity-concert/", "green"),
    ("SPORTS & ENTERTAINMENT", "Geosteady: Lugogo Concert Is Not on My Bucket List", "https://www.galaxyfm.co.ug/2026/09/12/geosteady-lugogo-concert-is-not-on-my-bucket-list/", ""),
    ("ENTERTAINMENT", "Mesach Semakula set to celebrate 50 years with mega concert", "https://bigeye.ug/mesach-semakula-set-to-celebrate-50-years-with-mega-concert/", ""),
    ("ENTERTAINMENT", "A Pass cites venue uncertainty as potential reason for moving from Kololo", "https://mbu.ug/2026/09/12/apass-reconsiders-kololo-concert-venue/", "red"),
    ("ENTERTAINMENT", "Kenneth Mugabi to Mark a Decade of 'Kibunomu' this Saturday", "https://softpower.ug/kenneth-mugabi-to-mark-a-decade-of-kibunomu-this-saturday/", "green"),
]

Headline.objects.all().delete()
for section_name, title, url, flag in sample:
    Headline.objects.create(
        title=title,
        url=url,
        section=sections[section_name],
        flag=flag,
        body="".join(f"<p>{p}</p>" for p in paragraphs(6, common=False)),
    )

# TOP STORIES go above the fold; the first one becomes the big splash headline.
Headline.objects.filter(section__name="TOP STORIES").update(is_top_story=True)

Image.objects.filter(title__startswith="seed-").delete()

# Real photos, keyed by headline title.
photos = [
    ("King Oyo buried as Omusuuga reaffirms new monarch", "https://i0.wp.com/observer.ug/wp-content/uploads/2026/09/King-Oyos-casket.jpg?resize=780%2C613&ssl=1"),
    ("Museveni asks Tooro to use legal means to resolve King Oyo succession dispute", "https://pmldaily.com/wp-content/uploads/2026/09/IMG_4159-654x375.jpeg"),
    ("Masaza Cup Quarter-Finals Kick Off as Eight Counties Chase Semi-Final Berths", "https://nilepost.co.ug/new_cms/wp-content/uploads/2026/09/a171d210-a5d3-491d-81cc-15c56fd88a2c.jpg"),
    ("Uganda ranks fifth globally for entry openness as passport mobility score stands at 70", "https://www.watchdoguganda.com/wp-content/uploads/2021/05/passport.jpeg"),
]
for title, src in photos:
    req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    h = Headline.objects.get(title=title)
    h.image = Image.objects.create(
        title=f"seed-{h.pk}", file=ImageFile(BytesIO(data), name=f"seed-{h.pk}.jpg")
    )
    h.save()

# Grey placeholders scattered Drudge-style: odd spots and shapes, not one per section.
placeholders = [
    ("Northern Bypass has nine of Kampala's 10 major crash hotspots", (400, 300)),
    ("Mesach Semakula set to celebrate 50 years with mega concert", (400, 560)),
]
for title, size in placeholders:
    h = Headline.objects.get(title=title)
    buf = BytesIO()
    PILImage.new("RGB", size, (90 + h.pk * 13 % 120,) * 3).save(buf, "PNG")
    h.image = Image.objects.create(
        title=f"seed-{h.pk}", file=ImageFile(buf, name=f"seed-{h.pk}.png")
    )
    h.save()

print(f"Seeded {Headline.objects.count()} headlines")
print("Done.")
