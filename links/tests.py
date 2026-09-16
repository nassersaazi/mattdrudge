from django.test import TestCase
from wagtail.models import Page, Site

from links.models import Headline, HomePage, Section


class HomePageTest(TestCase):
    def test_front_page_layout(self):
        home = Page.get_first_root_node().add_child(
            instance=HomePage(title="Home", slug="front")
        )
        Site.objects.update(root_page=home, site_name="Munnakampala")

        left = Section.objects.create(name="Left", column=1)
        Section.objects.create(name="Empty", column=2)
        right = Section.objects.create(name="Right", column=3)
        Headline.objects.create(title="Splash-headline", url="https://www.observer.ug/a", section=left, is_top_story=True)
        Headline.objects.create(title="Side-headline", url="https://example.test/b", section=left, is_top_story=True, sort_order=1)
        Headline.objects.create(title="Right-headline", url="https://example.test/c", section=right)

        html = self.client.get("/").content.decode()

        self.assertRegex(html, r"<title>\s*Munnakampala\s*</title>")
        # Top stories render once each: not in the latest rail or the section band.
        self.assertEqual(html.count("Splash-headline"), 1)
        self.assertEqual(html.count("Side-headline"), 1)
        # Order: masthead, side stories, splash, rail, band.
        self.assertLess(html.index('class="masthead"'), html.index("Side-headline"))
        self.assertLess(html.index("Side-headline"), html.index("Splash-headline"))
        self.assertLess(html.index('class="rail"'), html.index('class="band"'))
        # Three pinned columns; the empty section renders no block; right section lands in the last column.
        self.assertEqual(html.count('class="band-col"'), 3)
        self.assertEqual(html.count('class="block"'), 1)
        self.assertGreater(html.rindex("Right-headline"), html.rindex('class="band-col"'))
        # Bylines: known outlets get a display name, others fall back to the hostname.
        self.assertIn("The Observer", html)
        self.assertIn("example.test", html)
        # Footer: section links.
        self.assertIn('href="/#right"', html)

    def test_story_page(self):
        home = Page.get_first_root_node().add_child(
            instance=HomePage(title="Home", slug="front")
        )
        Site.objects.update(root_page=home, site_name="Munnakampala")
        section = Section.objects.create(name="News")
        story = Headline.objects.create(title="Story-headline", url="https://observer.ug/x", section=section, body="<p>Lorem ipsum</p>")
        external = Headline.objects.create(title="Link-headline", url="https://observer.ug/y", section=section)

        # Front page: headlines with a body open their story page; the rest link to the source.
        home_html = self.client.get("/").content.decode()
        self.assertIn(f'href="/story/{story.pk}/"', home_html)
        self.assertIn('href="https://observer.ug/y"', home_html)

        html = self.client.get(f"/story/{story.pk}/").content.decode()
        self.assertRegex(html, r"<title>\s*Story-headline\s*— Munnakampala\s*</title>")
        self.assertIn("<p>Lorem ipsum</p>", html)
        self.assertIn('href="https://observer.ug/x"', html)
        # No story page for headlines without a body, or unknown ids.
        self.assertEqual(self.client.get(f"/story/{external.pk}/").status_code, 404)
        self.assertEqual(self.client.get("/story/999999/").status_code, 404)
