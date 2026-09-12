"""Seed the Manyabino Report aggregator with sections + sample headlines.

Run with:
    python manage.py shell -c "exec(open('seed.py').read())"
"""
import urllib.request
from io import BytesIO

from django.core.files.images import ImageFile
from PIL import Image as PILImage
from wagtail.images.models import Image
from wagtail.models import Page, Site

from links.models import Headline, HomePage, Section

# 1. Remove Wagtail's default "Welcome" page (slug 'home') and its Site.
welcome = Page.objects.filter(slug="home", depth=2).first()
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
site.site_name = "gampe"
site.save()
print(f"Site: {site.site_name}")

# 4. Sections (columns).
section_specs = [
    # (name, sort_order, column)
    ("TOP STORIES", 0, 1),
    ("NATIONAL", 1, 1),
    ("SOCIETY", 2, 1),
    ("POLITICS", 3, 2),
    ("SPORTS", 4, 2),
    ("BUSINESS", 5, 3),
]
Section.objects.exclude(name__in=[s[0] for s in section_specs]).delete()
sections = {}
for name, order, column in section_specs:
    sections[name], _ = Section.objects.update_or_create(
        name=name, defaults={"sort_order": order, "column": column}
    )

# 5. Sample headlines: (section, title, url, flag).
# Uganda-only: real headlines from Ugandan outlets' RSS feeds, 12 Sep 2026.
sample = [
    ("TOP STORIES", "King Oyo buried as Omusuuga reaffirms new monarch", "https://observer.ug/news/king-oyo-buried-as-omusuuga-reaffirms-new-monarch/", ""),
    ("TOP STORIES", "Museveni calls for peaceful resolution of Tooro succession dispute", "https://www.monitor.co.ug/uganda/news/national/museveni-calls-for-peaceful-resolution-of-tooro-succession-dispute-5593202", "red"),
    ("TOP STORIES", "Uganda's first oil delayed yet again, new target pushed to June 2027", "https://observer.ug/business/ugandas-first-oil-delayed-yet-again-new-target-pushed-to-june-2027/", ""),
    ("NATIONAL", "Museveni orders review of plan to turn Kampala City Square into hotel", "https://observer.ug/news/museveni-orders-review-of-plan-to-turn-kampala-city-square-into-hotel/", ""),
    ("NATIONAL", "Northern Bypass has nine of Kampala's 10 major crash hotspots", "https://www.independent.co.ug/northern-bypass-has-nine-of-kampalas-10-major-crash-hotspots/", ""),
    ("NATIONAL", "'God has remembered us': Gomba celebrates lifeline rain after five-month dry spell", "https://nilepost.co.ug/news/370464/god-has-remembered-us-gomba-celebrates-lifeline-rain-after-five-month-dry-spell", "green"),
    ("SOCIETY", "Ageing Soroti Hospital needs urgent replacement", "https://www.independent.co.ug/ageing-soroti-hospital-needs-urgent-replacement/", ""),
    ("SOCIETY", "EXPERTS: Uganda's education export boom built without a strategy", "https://www.independent.co.ug/experts-ugandas-education-export-boom-built-without-a-strategy/", ""),
    ("SOCIETY", "Uganda ranks fifth globally for entry openness as passport mobility score stands at 70", "https://www.watchdoguganda.com/news/20260912/197967/uganda-ranks-fifth-globally-for-entry-openness-as-passport-mobility-score-stands-at-70.html", ""),
    ("POLITICS", "346 election petitions set for marathon hearing", "https://www.monitor.co.ug/uganda/news/national/346-election-petitions-set-for-marathon-hearing-5593080", ""),
    ("POLITICS", "Ssenyonyi warns against giving away City Square, recalls controversial land deals", "https://pmldaily.com/news/2026/09/ssenyonyi-warns-against-giving-away-city-square-recalls-controversial-land-deals.html", "red"),
    ("POLITICS", "Journalists walk out on police over blockade at Tooro palace", "https://observer.ug/news/journalists-walk-out-on-police-over-blockade-at-tooro-palace/", ""),
    ("SPORTS", "Kitara eliminate Mogadishu City Council to book Al Ahly at next stage", "https://kawowo.com/2026/09/12/kitara-eliminate-mogadishu-city-council-to-book-al-ahly-at-next-stage-caf-confederation-cup/", "green"),
    ("SPORTS", "Kenya inflicts first defeat on Cricket Cranes at ILT20 Cup", "https://kawowo.com/2026/09/12/kenya-inflicts-first-defeat-on-cricket-cranes-at-ilt20-cup/", ""),
    ("SPORTS", "Masaza Cup Quarter-Finals Kick Off as Eight Counties Chase Semi-Final Berths", "https://nilepost.co.ug/sports/370430/masaza-cup-quarter-finals-kick-off-as-eight-counties-chase-semi-final-berths", ""),
    ("BUSINESS", "Entebbe airport passenger traffic rises in August", "https://nilepost.co.ug/news/370460/entebbe-airport-passenger-traffic-rises-in-august", ""),
    ("BUSINESS", "Ugandan farmers count heavy losses as drought withers crops, weakens livestock", "https://www.independent.co.ug/ugandan-farmers-count-heavy-losses-as-drought-withers-crops-weakens-livestock/", ""),
    ("BUSINESS", "Busoga eyes coffee, cocoa tourism to create jobs", "https://www.monitor.co.ug/uganda/news/national/busoga-eyes-coffee-cocoa-tourism-to-create-jobs-5592852", ""),
]

Headline.objects.all().delete()
for section_name, title, url, flag in sample:
    Headline.objects.create(
        title=title,
        url=url,
        section=sections[section_name],
        flag=flag,
    )

# TOP STORIES go above the fold; the first one becomes the big splash headline.
Headline.objects.filter(section__name="TOP STORIES").update(is_top_story=True)

Image.objects.filter(title__startswith="seed-").delete()

# Real photo for the splash headline (first TOP STORIES headline).
splash = sections["TOP STORIES"].headlines.order_by("id").first()
req = urllib.request.Request(
    "https://i0.wp.com/observer.ug/wp-content/uploads/2026/09/King-Oyos-casket.jpg?resize=780%2C613&ssl=1",
    headers={"User-Agent": "Mozilla/5.0"},
)
with urllib.request.urlopen(req, timeout=30) as resp:
    splash.image = Image.objects.create(
        title="seed-king-oyo-casket",
        file=ImageFile(BytesIO(resp.read()), name="seed-king-oyo-casket.jpg"),
    )
splash.save()

# Grey placeholders on the first headline of each other section, and the second top story.
for section in sections.values():
    qs = section.headlines.order_by("id")
    for h in qs[1:2] if section.name == "TOP STORIES" else qs[:1]:
        buf = BytesIO()
        PILImage.new("RGB", (400, 400), (90 + h.pk * 13 % 120,) * 3).save(buf, "PNG")
        h.image = Image.objects.create(
            title=f"seed-{h.pk}", file=ImageFile(buf, name=f"seed-{h.pk}.png")
        )
        h.save()

print(f"Seeded {Headline.objects.count()} headlines")
print("Done.")
