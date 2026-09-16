from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render

from links.models import Headline, Section


def story(request, pk):
    headline = get_object_or_404(
        Headline.objects.select_related("section", "image").exclude(body=""), pk=pk
    )
    # Same nav as the front page: only sections with headlines in the band.
    sections = Section.objects.prefetch_related(
        Prefetch("headlines", queryset=Headline.objects.filter(is_top_story=False))
    )
    return render(request, "links/story.html", {"h": headline, "sections": sections})
