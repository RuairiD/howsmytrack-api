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
    inlines = [
        FeedbackRequestInline
    ]

admin.site.register(FeedbackGroupsUser)
admin.site.register(FeedbackGroup, FeedbackGroupAdmin)
admin.site.register(FeedbackRequest)
admin.site.register(FeedbackResponse)
