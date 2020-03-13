from django.contrib import admin
from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse
from howsmytrack.core.models import FeedbackResponseReply


class FeedbackRequestInline(admin.TabularInline):
    raw_id_fields = ['user']
    model = FeedbackRequest
    max_num = 4
    extra = 0


class FeedbackGroupAdmin(admin.ModelAdmin):
    fields = ('name', )
    search_fields = ['name']
    inlines = [
        FeedbackRequestInline
    ]


class FeedbackGroupsUserAdmin(admin.ModelAdmin):
    search_fields = ['user__username']
    list_display = (
        'username',
        'rating',
        'date_joined'
    )
    inlines = [
        FeedbackRequestInline
    ]

    def username(self, obj):
        return obj.user.username

    def date_joined(self, obj):
        return obj.user.date_joined


class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'feedback_request_submitted_username',
        'feedback_request_media_url',
        'feedback',
        'submitted',
        'rating',
    )
    search_fields = ['user__user__username']
    raw_id_fields = ['feedback_request', 'user']

    def feedback_request_submitted_username(self, obj):
        return obj.feedback_request.user.email

    def feedback_request_media_url(self, obj):
        return obj.feedback_request.media_url


class FeedbackResponseReplyAdmin(admin.ModelAdmin):
    search_fields = ['user__username']
    raw_id_fields = ['feedback_response', 'user']
    list_display = (
        'user',
        'feedback_response',
        'text',
        'allow_replies',
        'time_created',
    )


class FeedbackRequestAdmin(admin.ModelAdmin):
    raw_id_fields = ['user']
    list_display = (
        'user',
        'media_url',
        'media_type',
        'genre',
        'time_created',
        'feedback_group',
    )
    search_fields = ['user__user__username']


admin.site.register(FeedbackGroupsUser, FeedbackGroupsUserAdmin)
admin.site.register(FeedbackGroup, FeedbackGroupAdmin)
admin.site.register(FeedbackRequest, FeedbackRequestAdmin)
admin.site.register(FeedbackResponse, FeedbackResponseAdmin)
admin.site.register(FeedbackResponseReply, FeedbackResponseReplyAdmin)
