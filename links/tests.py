from django.test import TestCase
from wagtail.models import Page, Site

from links.models import Headline, HomePage, Section


class HomePageTest(TestCase):
    def test_front_page_layout(self):
        home = Page.get_first_root_node().add_child(
            instance=HomePage(title="Home", slug="front")
        )
        Site.objects.update(root_page=home, site_name="gampe")

        left = Section.objects.create(name="Left", column=1)
        Section.objects.create(name="Empty", column=2)
        right = Section.objects.create(name="Right", column=3)
        url = "https://example.test/"
        Headline.objects.create(title="Splash-headline", url=url, section=left, is_top_story=True)
        Headline.objects.create(title="Fold-headline", url=url, section=left, is_top_story=True, sort_order=1)
        Headline.objects.create(title="Right-headline", url=url, section=right)

        html = self.client.get("/").content.decode()

        self.assertRegex(html, r"<title>\s*gampe\s*</title>")
        # Top stories render once each, not repeated in the columns.
        self.assertEqual(html.count("Splash-headline"), 1)
        self.assertEqual(html.count("Fold-headline"), 1)
        # Order: above the fold, splash, masthead, columns.
        self.assertLess(html.index("Fold-headline"), html.index("Splash-headline"))
        self.assertLess(html.index("Splash-headline"), html.index('class="masthead"'))
        # Three pinned columns; the empty section renders no group; right section lands in the last column.
        self.assertEqual(html.count('class="column"'), 3)
        self.assertEqual(html.count('class="group"'), 1)
        self.assertGreater(html.index("Right-headline"), html.rindex('class="column"'))
