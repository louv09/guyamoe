from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse

from misc.models import Page
from reader.models import Chapter, Series


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7
    protocol = "https"

    def items(self):
        return ["site-home", "site-about", "site-oneshots", "site-series", "site-chapters"]

    def location(self, item):
        return reverse(item)


class SeriesViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5
    protocol = "https"

    def items(self):
        return Series.objects.all()


class ChapterViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.4
    protocol = "https"

    def items(self):
        return Chapter.objects.filter(series__isnull=False, is_public=True).order_by(
            "series__id", "-chapter_number"
        )


class PagesListViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5
    protocol = "https"

    def items(self):
        pages = Page.objects.all()
        return [pages[0]] if len(pages) > 0 else []

    def location(self, item):
        return "/pages"


class PageViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5
    protocol = "https"

    def items(self):
        return Page.objects.all().order_by("-date")
