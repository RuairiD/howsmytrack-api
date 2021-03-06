from django.contrib import admin

from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse
from howsmytrack.core.models import FeedbackResponseReply


class FeedbackRequestInline(admin.TabularInline):
    raw_id_fields = ["user"]
    model = FeedbackRequest
    max_num = 4
    extra = 0


class FeedbackResponseInline(admin.TabularInline):
    raw_id_fields = ["user", "feedback_request"]
    model = FeedbackResponse
    max_num = 8
    extra = 0


class FeedbackGroupAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = (
        "name",
        "time_created",
    )
    inlines = [FeedbackRequestInline]


class FeedbackGroupsUserAdmin(admin.ModelAdmin):
    search_fields = ["user__username"]
    list_display = (
        "username",
        "rating",
        "date_joined",
        "send_reminder_emails",
    )
    inlines = [FeedbackRequestInline]

    def username(self, obj):
        return obj.user.username

    def date_joined(self, obj):
        return obj.user.date_joined


class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "feedback_request_submitted_username",
        "feedback_request_media_url",
        "feedback",
        "submitted",
        "rating",
        "allow_replies",
    )
    search_fields = ["user__user__username"]
    raw_id_fields = ["feedback_request", "user"]

    def feedback_request_submitted_username(self, obj):
        return obj.feedback_request.user.email

    def feedback_request_media_url(self, obj):
        return obj.feedback_request.media_url


class FeedbackResponseReplyAdmin(admin.ModelAdmin):
    search_fields = ["user__username"]
    raw_id_fields = ["feedback_response", "user"]
    list_display = (
        "user",
        "feedback_response",
        "text",
        "allow_replies",
        "time_created",
    )


class FeedbackRequestAdmin(admin.ModelAdmin):
    raw_id_fields = ["user"]
    list_display = (
        "user",
        "media_url",
        "media_type",
        "genre",
        "time_created",
        "feedback_group",
    )
    search_fields = ["user__user__username"]
    inlines = [
        FeedbackResponseInline,
    ]


admin.site.register(FeedbackGroupsUser, FeedbackGroupsUserAdmin)
admin.site.register(FeedbackGroup, FeedbackGroupAdmin)
admin.site.register(FeedbackRequest, FeedbackRequestAdmin)
admin.site.register(FeedbackResponse, FeedbackResponseAdmin)
admin.site.register(FeedbackResponseReply, FeedbackResponseReplyAdmin)
