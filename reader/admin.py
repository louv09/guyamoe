from datetime import datetime, timezone

from django.contrib import admin
from django.utils.html import escape, linebreaks

from .forms import ChapterForm, SeriesForm
from .models import Chapter, Group, HitCount, Person, Series, Volume



class HitCountAdmin(admin.ModelAdmin):
    ordering = ("hits",)
    list_display = (
        "hits",
        "content",
        "series",
        "content_type",
    )

    def series(self, obj):
        if isinstance(obj.content, Series):
            return obj.content.name
        if isinstance(obj.content, Chapter):
            return obj.content.series.name
        else:
            return obj

admin.site.register(HitCount, HitCountAdmin)


class PersonAdmin(admin.ModelAdmin):
    ordering = ("name",)
    list_display = (
        "name",
        "slug",
    )
    search_fields = (
        "name",
        "slug",
    )


admin.site.register(Person, PersonAdmin)


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
    )


admin.site.register(Group, GroupAdmin)


class SeriesAdmin(admin.ModelAdmin):
    form = SeriesForm
    list_display = ("name", "author")
    search_fields = (
        "name",
        "author__name",
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["synopsis"].help_text = 'Here is an example of how to set the author\'s link:\n' + linebreaks(escape('\n\
         <a href=""><img src="https://i.imgur.com/dQCXZkU.png" alt="twitter"/>Artist\'s Twitter</a>\n\
         <a href=""><img src="https://i.imgur.com/oiVINmy.png" alt="pixiv"/>Artist\'s Pixiv</a>\n\
         <a href=""><img src="https://i.imgur.com/NVVf9Jl.png" alt="MelonBook"/>Artist\'s MelonBook</a>\n\
         <a href=""><img src="https://i.imgur.com/DByqIm6.png" alt="FanBox"/>Artist\'s FANBOX</a>\n\
         <a href=""><img src="https://i.imgur.com/5Wohzas.png" alt="BOOTH"/>Artist\'s BOOTH</a>\n\
         <a href=""><img src="https://i.imgur.com/H1Q0eHg.png" alt="NicoVideo"/>Artist\'s Nico</a>\n\
         <a href=""><img src="https://i.imgur.com/mLCeebg.png" alt="Skeb"/>Artist\'s Skeb</a>\n\
         <a href=""><img src="https://i.imgur.com/qr4qCHu.png" alt="Fantia"/>Artist\'s Fantia</a>\n\
         <a href=""><img src="https://i.imgur.com/gpw5ezu.png" alt="Tumblr"/>Artist\'s Tumblr</a>\n\
         <a href=""><img src="https://i.imgur.com/TysezOa.png" alt="Youtube"/>Artist\'s Youtube</a>\n\
         <a href=""><img src="https://i.imgur.com/dzEFKZB.png" alt="Personal Website"/>Artist\'s Website</a>\n\
         \n'))
        return form


admin.site.register(Series, SeriesAdmin)


class VolumeAdmin(admin.ModelAdmin):
    search_fields = (
        "volume_number",
        "series__name",
    )
    ordering = ("volume_number",)
    list_display = (
        "volume_number",
        "series",
        "volume_cover",
    )

    exclude = ("volume_cover ",)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ()
        else:
            return ("volume_cover",)


admin.site.register(Volume, VolumeAdmin)


class ChapterAdmin(admin.ModelAdmin):
    form = ChapterForm
    search_fields = (
        "chapter_number",
        "title",
        "series__name",
        "volume",
    )
    list_display = (
        "chapter_number",
        "title",
        "series",
        "volume",
        "version",
        "time_since_last_update",
        "updated_on",
        "uploaded_on",
    )

    def get_queryset(self, request):
        qs = super(ChapterAdmin, self).get_queryset(request)
        sort_sql = """SELECT
CASE
    WHEN updated_on IS NOT NULL THEN updated_on
    ELSE uploaded_on END
as time_since_change
"""
        qs = qs.extra(select={"time_since_last_update": sort_sql}).order_by(
            "-time_since_last_update"
        )
        return qs

    def time_since_last_update(self, obj):
        curr_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        if obj.time_since_last_update is not None:
            if isinstance(obj.time_since_last_update, str):
                try:
                    last_update = last_update = datetime.strptime(obj.time_since_last_update, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    last_update = datetime.strptime(obj.time_since_last_update, "%Y-%m-%d %H:%M:%S")
                last_update = last_update.replace(tzinfo=timezone.utc)
            else:
                last_update = last_update.replace(tzinfo=timezone.utc)
            time_diff = curr_time - last_update
        elif obj.uploaded_on is not None:
            time_diff = curr_time - obj.uploaded_on
        else:
            return "Unknown"
        days = time_diff.days
        seconds = time_diff.seconds
        hours = seconds // 3600
        minutes = (seconds // 60) % 60

        return f"{days} days {hours} hours {minutes} mins"

    time_since_last_update.admin_order_field = "time_since_last_update"
    ordering = ("-uploaded_on", "-updated_on")


admin.site.register(Chapter, ChapterAdmin)
