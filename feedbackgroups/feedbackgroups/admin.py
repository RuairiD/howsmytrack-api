from django.contrib import admin
from feedbackgroups.feedbackgroups.models import FeedbackGroupsUser
from feedbackgroups.feedbackgroups.models import FeedbackGroup
from feedbackgroups.feedbackgroups.models import FeedbackRequest
from feedbackgroups.feedbackgroups.models import FeedbackResponse

admin.site.register(FeedbackGroupsUser)
admin.site.register(FeedbackGroup)
admin.site.register(FeedbackRequest)
admin.site.register(FeedbackResponse)
