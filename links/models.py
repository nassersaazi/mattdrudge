from django.db import models
from django.db.models import Prefetch
from django.utils.text import slugify

from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.images.models import Image
from wagtail.models import Page
from wagtail.snippets.models import register_snippet


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
    """A single external link headline."""

    FLAG_CHOICES = [
        ("", "None"),
        ("red", "Red (breaking)"),
        ("green", "Green"),
    ]

    title = models.CharField(max_length=300)
    url = models.URLField(max_length=1000)
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
        )
    ]

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Headline"
        verbose_name_plural = "Headlines"

    def __str__(self):
        return self.title


class HomePage(Page):
    """The Drudge-style front page."""

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
        context["top_stories"] = list(headlines.filter(is_top_story=True))
        return context

    class Meta:
        verbose_name = "Home"
