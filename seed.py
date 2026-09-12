"""Seed the Manyabino Report aggregator with sections + sample headlines.

Run with:
    python manage.py shell -c "exec(open('seed.py').read())"
"""
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
    ("TOP STORIES", 0),
    ("WORLD", 1),
    ("POLITICS", 2),
    ("BUSINESS", 3),
    ("TECH", 4),
    ("SCIENCE & HEALTH", 5),
]
sections = {}
for name, order in section_specs:
    obj, created = Section.objects.get_or_create(
        name=name, defaults={"sort_order": order}
    )
    if not created:
        obj.sort_order = order
        obj.save()
    sections[name] = obj

# 5. Sample headlines: (section, title, url, flag).
sample = [
    ("TOP STORIES", "Markets steady as investors weigh rate outlook", "https://www.reuters.com/markets/", ""),
    ("TOP STORIES", "Diplomats push for new ceasefire talks", "https://apnews.com/world-news", "red"),
    ("TOP STORIES", "Storm system gains strength in the Atlantic", "https://www.bbc.com/news/world", ""),
    ("WORLD", "Election monitors report high turnout", "https://www.bbc.com/news/world", ""),
    ("WORLD", "Historic summit opens in Geneva", "https://www.aljazeera.com/", ""),
    ("WORLD", "Aid convoy reaches besieged region", "https://www.reuters.com/world/", "green"),
    ("POLITICS", "Lawmakers clash over spending bill", "https://www.reuters.com/world/us/", ""),
    ("POLITICS", "New poll shows tight race heading into autumn", "https://www.politico.com/", "red"),
    ("POLITICS", "Senate schedules vote on key nomination", "https://www.bbc.com/news/world/us_and_canada", ""),
    ("BUSINESS", "Oil prices slip on supply outlook", "https://www.reuters.com/business/energy/", ""),
    ("BUSINESS", "Big tech earnings beat expectations", "https://www.cnbc.com/tech/", ""),
    ("BUSINESS", "Central bank signals patient approach", "https://www.reuters.com/markets/rates-bonds/", ""),
    ("TECH", "Chipmaker unveils next-generation processor", "https://www.theverge.com/", ""),
    ("TECH", "AI startup raises record funding round", "https://techcrunch.com/", "red"),
    ("TECH", "Regulators open inquiry into app store", "https://www.reuters.com/technology/", ""),
    ("SCIENCE & HEALTH", "Study links diet to lower disease risk", "https://www.nih.gov/news-events", ""),
    ("SCIENCE & HEALTH", "New telescope captures distant galaxy", "https://www.nasa.gov/", ""),
    ("SCIENCE & HEALTH", "Vaccine trial shows promising results", "https://www.who.int/news", "green"),
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

print(f"Seeded {Headline.objects.count()} headlines")
print("Done.")
