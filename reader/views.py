import json
from collections import OrderedDict, defaultdict
from datetime import datetime
import os

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import decorator_from_middleware
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt

from .middleware import OnlineNowMiddleware
from .models import Chapter, HitCount, Series, Volume
from .users_cache_lib import get_user_ip


@csrf_exempt
@decorator_from_middleware(OnlineNowMiddleware)
def hit_count(request):
    if request.method == "POST":
        user_ip = get_user_ip(request)
        page_id = f"url_{request.POST['series']}/{request.POST['chapter'] if 'chapter' in request.POST else ''}{user_ip}"
        if not cache.get(page_id):
            cache.set(page_id, page_id, 60)
            series_slug = request.POST["series"]
            series_id = Series.objects.get(slug=series_slug).id
            series = ContentType.objects.get(app_label="reader", model="series")
            hit, _ = HitCount.objects.get_or_create(
                content_type=series, object_id=series_id
            )
            hit.hits = F("hits") + 1
            hit.save()
            if "chapter" in request.POST:
                chapter_number = request.POST["chapter"]
                group_id = request.POST["group"]
                chapter = ContentType.objects.get(app_label="reader", model="chapter")
                ch_obj = Chapter.objects.filter(
                    chapter_number=float(chapter_number),
                    group__id=group_id,
                    series__id=series_id,
                ).first()
                if ch_obj:
                    hit, _ = HitCount.objects.get_or_create(
                        content_type=chapter, object_id=ch_obj.id,
                    )
                    hit.hits = F("hits") + 1
                    hit.save()

    return HttpResponse(json.dumps({}), content_type="application/json")


def series_page_data(series_slug, show_private_chapters=False):
    series_page_dt = cache.get(f"series_page_dt_{series_slug}_{show_private_chapters}")
    if not series_page_dt:
        series = get_object_or_404(Series, slug=series_slug)
        chapters = Chapter.objects.filter(series=series)
        if not show_private_chapters:
            chapters = chapters.filter(is_public=True)
        chapters.select_related(
            "series", "group"
        )
        latest_chapter = chapters.latest("uploaded_on") if chapters else None
        vols = Volume.objects.filter(series=series).order_by("-volume_number")
        cover_vol_url = ""
        cover_vol_url_webp = ""
        cover_vol_width_height = (0, 0)
        for vol in vols:
            if vol.volume_cover:
                cover_vol_url = f"/media/{vol.volume_cover}"
                cover_vol_url_webp = cover_vol_url.rsplit(".", 1)[0] + ".webp"
                cover_vol_width_height = (vol.volume_cover.width, vol.volume_cover.height)
                break
        content_series = ContentType.objects.get(app_label="reader", model="series")
        hit, _ = HitCount.objects.get_or_create(
            content_type=content_series, object_id=series.id
        )
        chapter_list = []
        volume_dict = defaultdict(list)
        chapter_dict = OrderedDict()
        for chapter in chapters:
            ch_clean = chapter.clean_chapter_number()
            if ch_clean in chapter_dict:
                if chapter.uploaded_on > chapter_dict[ch_clean][0].uploaded_on:
                    chapter_dict[ch_clean] = [chapter, True]
                else:
                    chapter_dict[ch_clean] = [chapter_dict[ch_clean][0], True]
            else:
                chapter_dict[ch_clean] = [chapter, False]

        chapter_content_type = ContentType.objects.get(app_label="reader", model="chapter")
        chapters_hit_count = HitCount.objects.filter(content_type=chapter_content_type).all()
        id_to_hit_count = {int(hit_count.object_id) : int(hit_count.hits) for hit_count in chapters_hit_count}
        for ch in chapter_dict:
            chapter, multiple_groups = chapter_dict[ch]
            u = chapter.uploaded_on
            chapter_list.append(
                [
                    chapter.clean_chapter_number(),
                    chapter.clean_chapter_number(),
                    chapter.title,
                    chapter.slug_chapter_number(),
                    chapter.group.name if not multiple_groups else "Multiple Groups",
                    [u.year, u.month - 1, u.day, u.hour, u.minute, u.second],
                    chapter.volume or "null",
                    id_to_hit_count.get(int(chapter.id), 0),
                    chapter.scraper_hash,
                    chapter.is_public
                ]
            )
            volume_dict[chapter.volume].append(
                [
                    chapter.clean_chapter_number(),
                    chapter.slug_chapter_number(),
                    chapter.group.name if not multiple_groups else "Multiple Groups",
                    [u.year, u.month - 1, u.day, u.hour, u.minute, u.second]
                ]
            )
        volume_list = []
        for key, value in volume_dict.items():
            volume_list.append(
                [key, sorted(value, key=lambda x: float(x[0]), reverse=True)]
            )
        chapter_list.sort(key=lambda x: float(x[0]), reverse=True)
        available_features = [
                "detailed",
                "rss",
                "volumeCovers",
            ]
        if settings.ALLOWS_DOWNLOAD_AS_ZIP:
            available_features += ["download"]
        if len(chapter_list) > 5:
            available_features += ["compact"]
        series_page_dt = {
            "series": series.name,
            "alt_titles": series.alternative_titles.split(", ")
            if series.alternative_titles
            else [],
            "alt_titles_str": f" Alternative titles: {series.alternative_titles}."
            if series.alternative_titles
            else "",
            "series_id": series.id,
            "slug": series.slug,
            "cover_vol_url": cover_vol_url,
            "cover_vol_url_webp": cover_vol_url_webp,
            "cover_vol_width": int(cover_vol_width_height[0]),
            "cover_vol_height": int(cover_vol_width_height[1]),
            "metadata": [
                ["Author", series.author.name, series.author.get_absolute_url()],
                ["Artist", series.artist.name, series.artist.get_absolute_url()],
                ["Views", hit.hits + 1, None],
                [
                    "Last Updated",
                    f"Ch. {latest_chapter.clean_chapter_number() if latest_chapter else ''} - {datetime.utcfromtimestamp(latest_chapter.uploaded_on.timestamp()).strftime('%Y-%m-%d') if latest_chapter else ''}",
                    None,
                ],
            ],
            "synopsis": series.synopsis,
            "author": series.author.name,
            "is_nsfw": bool(series.is_nsfw),
            "chapter_list": chapter_list,
            "volume_list": sorted(volume_list, key=lambda m: m[0], reverse=True),
            "root_domain": settings.CANONICAL_ROOT_DOMAIN,
            "relative_url": f"read/manga/{series.slug}/",
            "available_features": available_features,
            "reader_modifier": "read/manga",
            "discord_notification_enabled": settings.DISCORD_PRERELEASE_WEBHOOK_URL != "",
        }
        if series.scraping_uuid:
            series_page_dt["metadata"].append(["Link", 'On MangaDex', f"https://mangadex.org/title/{str(series.scraping_uuid)}"])
        cache.set(f"series_page_dt_{series_slug}_{show_private_chapters}", series_page_dt, 3600 * 12)
    return series_page_dt


@cache_control(public=True, max_age=60, s_maxage=60)
@decorator_from_middleware(OnlineNowMiddleware)
def series_info(request, series_slug):
    data = series_page_data(series_slug)
    data["version_query"] = settings.STATIC_VERSION
    return render(request, "reader/series.html", data)


@staff_member_required
@cache_control(public=True, max_age=60, s_maxage=60)
@decorator_from_middleware(OnlineNowMiddleware)
def series_info_admin(request, series_slug):
    data = series_page_data(series_slug, show_private_chapters=True)
    data["version_query"] = settings.STATIC_VERSION
    data["available_features"].append("admin")
    return render(request, "reader/series.html", data)


def get_all_metadata(series_slug, slug_chapter_number):
    series_metadata = cache.get(f"series_metadata_{series_slug}_{slug_chapter_number}")
    if not series_metadata:
        series = Series.objects.filter(slug=series_slug).first()
        if not series:
            return None
        chapters = Chapter.objects.filter(series=series).select_related("series", "group")
        series_metadata = {}
        series_metadata["indexed"] = series.indexed
        for chapter in chapters:
            if chapter.slug_chapter_number() != slug_chapter_number:
                continue

            first_page_url = chapter.first_page_absolute_url()

            series_metadata[chapter.slug_chapter_number()] = {
                "series_id": int(chapter.series.id),
                "series_name": chapter.series.name,
                "slug": chapter.series.slug,
                "author_name": series.author.name,
                "is_nsfw": bool(series.is_nsfw),
                "chapter_number": chapter.clean_chapter_number(),
                "chapter_title": chapter.title,
                "first_page_url": first_page_url
            }
        cache.set(f"series_metadata_{series_slug}_{slug_chapter_number}", series_metadata, 3600 * 12)
    return series_metadata


@cache_control(public=True, max_age=30, s_maxage=30)
@decorator_from_middleware(OnlineNowMiddleware)
def reader(request, series_slug, chapter, page=None):
    if page:
        data = get_all_metadata(series_slug, chapter)
        if data and chapter in data:
            data[chapter]["relative_url"] = f"read/manga/{series_slug}/{chapter}/1"
            data[chapter]["api_path"] = f"/api/series/"
            data[chapter]["image_proxy_url"] = settings.IMAGE_PROXY_URL
            data[chapter]["version_query"] = settings.STATIC_VERSION
            data[chapter]["first_party"] = True
            data[chapter]["indexed"] = data["indexed"]
            data[chapter]["can_download"] = settings.ALLOWS_DOWNLOAD_AS_ZIP
            return render(request, "reader/reader.html", data[chapter])
        else:
            return render(request, "homepage/how_cute_404.html", status=404)
    else:
        return redirect("reader-manga-chapter", series_slug, chapter, "1")
