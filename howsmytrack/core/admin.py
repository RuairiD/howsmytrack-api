from django.contrib import admin
from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse

admin.site.register(FeedbackGroupsUser)
admin.site.register(FeedbackGroup)
admin.site.register(FeedbackRequest)
admin.site.register(FeedbackResponse)
