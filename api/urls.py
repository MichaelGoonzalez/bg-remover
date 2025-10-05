from django.urls import path
from .views import RemoveBackgroundView, RemoveBackgroundView2, JurassicExplorerView

urlpatterns = [
    path('remove-background/', RemoveBackgroundView.as_view(), name='remove-background'),
    path('remove-background2/', RemoveBackgroundView2.as_view(), name='remove-background2'),
    path('jurassic-explorer/', JurassicExplorerView.as_view(), name='jurassic-explorer'),
]
