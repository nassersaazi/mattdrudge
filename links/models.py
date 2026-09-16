from urllib.parse import urlparse

from django.db import models
from django.db.models import Prefetch
from django.urls import reverse
from django.utils.text import slugify

from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.images.models import Image
from wagtail.models import Page
from wagtail.snippets.models import register_snippet

# Display names for known outlets; anything else shows its hostname.
OUTLETS = {
    "bigeye.ug": "Bigeye",
    "galaxyfm.co.ug": "Galaxy FM",
    "independent.co.ug": "The Independent",
    "mbu.ug": "MBU",
    "nilepost.co.ug": "Nile Post",
    "observer.ug": "The Observer",
    "pmldaily.com": "PML Daily",
    "softpower.ug": "SoftPower",
    "watchdoguganda.com": "Watchdog Uganda",
}


@register_snippet
class Section(models.Model):
    """A group of headlines, pinned to one of the three front-page columns."""

    COLUMN_CHOICES = [(1, "Left"), (2, "Middle"), (3, "Right")]

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    column = models.PositiveSmallIntegerField(choices=COLUMN_CHOICES, default=1)

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("column"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Section"
        verbose_name_plural = "Sections"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


@register_snippet
class Headline(models.Model):
    """A headline linking to its story page, or straight to the source if it has no body."""

    FLAG_CHOICES = [
        ("", "None"),
        ("red", "Red (breaking)"),
        ("green", "Green"),
    ]

    title = models.CharField(max_length=300)
    url = models.URLField(max_length=1000, help_text="Original article on the source outlet.")
    section = models.ForeignKey(
        Section, related_name="headlines", on_delete=models.CASCADE
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_top_story = models.BooleanField(
        default=False, help_text="Feature this in the big top-story block."
    )
    image = models.ForeignKey(
        Image,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    flag = models.CharField(
        max_length=10, blank=True, choices=FLAG_CHOICES, default=""
    )
    body = RichTextField(
        blank=True, help_text="Story text. Leave empty to link straight to the source."
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("title"),
                FieldPanel("url"),
                FieldPanel("section"),
                FieldPanel("sort_order"),
                FieldPanel("is_top_story"),
                FieldPanel("image"),
                FieldPanel("flag"),
            ],
            heading="Headline",
        ),
        FieldPanel("body"),
    ]

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Headline"
        verbose_name_plural = "Headlines"

    def __str__(self):
        return self.title

    @property
    def source(self):
        host = urlparse(self.url).netloc.lower().removeprefix("www.")
        return OUTLETS.get(host, host)

    @property
    def link(self):
        return reverse("story", args=[self.pk]) if self.body else self.url


class HomePage(Page):
    """The front page."""

    max_count = 1

    content_panels = Page.content_panels

    subpage_types = []

    def get_context(self, request):
        context = super().get_context(request)
        headlines = Headline.objects.select_related("image").prefetch_related(
            "image__renditions"
        ).order_by("sort_order", "id")
        sections = list(
            Section.objects.prefetch_related(
                Prefetch("headlines", queryset=headlines.filter(is_top_story=False))
            )
        )
        context["columns"] = [
            [s for s in sections if s.column == col]
            for col, _ in Section.COLUMN_CHOICES
        ]
        context["sections"] = sections
        context["top_stories"] = list(headlines.filter(is_top_story=True))
        context["latest"] = list(
            headlines.filter(is_top_story=False).order_by("-id")[:4]
        )
        return context

    class Meta:
        verbose_name = "Home"

