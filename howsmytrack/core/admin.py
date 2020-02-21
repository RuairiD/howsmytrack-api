from django.contrib import admin
from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse


class FeedbackRequestInline(admin.TabularInline):
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
        'user',
        'rating',
    )
    inlines = [
        FeedbackRequestInline
    ]


class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'feedback_request',
        'feedback',
        'submitted',
        'rating',
    )
    search_fields = ['user__user__username']


class FeedbackRequestAdmin(admin.ModelAdmin):
    list_display = ('user','media_url','media_type','time_created','feedback_group')
    search_fields = ['user__user__username']


admin.site.register(FeedbackGroupsUser, FeedbackGroupsUserAdmin)
admin.site.register(FeedbackGroup, FeedbackGroupAdmin)
admin.site.register(FeedbackRequest, FeedbackRequestAdmin)
admin.site.register(FeedbackResponse, FeedbackResponseAdmin)
