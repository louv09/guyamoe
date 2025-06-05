from django.urls import path, re_path
from django.conf import settings

from api import views

urlpatterns = [
    re_path(
        r"^series/(?P<series_slug>[\w-]+)/$",
        views.get_series_data,
        name="api-series_data",
    ),
    re_path(r"^get_all_series/", views.get_all_series, name="api-get-all-series"),
    re_path(
        r"^get_groups/(?P<series_slug>[\w-]+)/", views.get_groups, name="api-groups"
    ),
    re_path(r"^get_all_groups/", views.get_all_groups, name="api-all-groups"),
    # re_path(r'^download_volume/(?P<series_slug>[\w-]+)/(?P<volume>[\d]{1,9})', views.download_volume, name='api-volume-chapters-download'),
    re_path(
        r"^upload_new_chapter/(?P<series_slug>[\w-]+)/",
        views.upload_new_chapter,
        name="api-chapter-upload",
    ),
    re_path(
        r"^publish_chapter/(?P<series_slug>[\w-]+)/(?P<chapter>(\d+(\.\d+)?))",
        views.publish_chapter,
        name="api-publish-chapter",
    ),
    re_path(
        r"^upload_new_oneshot/",
        views.upload_new_oneshot,
        name="api-new-oneshot",
    ),
    re_path(
        r"^get_volume_covers/(?P<series_slug>[\w-]+)/",
        views.get_volume_covers,
        name="api-get-volume-covers",
    ),
    re_path(
        r"^search_index/(?P<series_slug>[\w-]+)/",
        views.search_index,
        name="api-search-index",
    ),
    re_path(r"clear_cache/", views.clear_cache, name="api-clear-cache"),
    re_path(r"^black_hole_mail/", views.black_hole_mail, name="api-black-hole-mail"),
]

if settings.ALLOWS_DOWNLOAD_AS_ZIP:
    urlpatterns.append(
        re_path(
            r"^download_chapter/(?P<series_slug>[\w-]+)/(?P<chapter>[\d-]{1,9})/$",
            views.download_chapter,
            name="api-chapter-download",
        )
    )